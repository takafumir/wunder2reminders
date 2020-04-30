# coding=utf-8

"""wunder2reminders.py

Usage:
  wunder2reminders.py FILE [options]

Options:
  --encoding=<codec>    [default: utf-8-sig].
  --output-path=<path>  [default: reminders].
  -h --help             Show this screen.
  --version             Show version.

"""

from docopt import docopt
import json
import codecs
import logging
from icalendar import Calendar, Todo
from datetime import datetime
import os
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger(__name__)

VERSION = '0.1.0'

def process(list):
    name = list['title'].replace('/','').replace(':','')
    task_count = len(list['tasks'])
    logger.debug('List "{}" with {} tasks (not counting subtasks)'.format(name, task_count))
    return createVCAL(list).to_ical(), name

def readFile(input, encoding='utf-8-sig'):
    logger.info('Read file {}'.format(input))
    return json.load(codecs.open(input, 'r', encoding))

def writeICSFiles(ical_data, name, dir):
    path = os.path.join(dir, '{}.ics'.format(name))
    f = open(path, 'wb')
    f.write(ical_data)
    logger.info('Save file {}'.format(path))
    f.close()

def createVCAL(list):
    cal = Calendar()
    for task in list['tasks']:
        for component in createVTODOs(task):
            cal.add_component(component)
    return cal

def createVTODOs(task, parent=None):
    todos = []
    todo = Todo()
    try:
        todo.add('UID', str(task['id']))
    except KeyError:
        todo.add('UID', str(uuid.uuid1()))
    try:
        todo.add('dtstamp', datetime.strptime(task['createdAt'], "%Y-%m-%dT%H:%M:%S.%f%z"))
    except ValueError: #Thank you for using different formats within the same field!
        try:
            todo.add('dtstamp', datetime.strptime(task['createdAt'], "%Y-%m-%dT%H:%M:%S%z"))
        except:
            logger.error('Could not parse creation date for Task {}'.format(task['id']))
            quit()
    todo.add('summary', task.get('title', ''))
    if task.get('dueDate', None) is not None:
        todo.add('DUE', datetime.strptime(task['dueDate'], "%Y-%m-%dT%H:%M:%S"))
    if task['completed']:
        todo.add('status', 'COMPLETED')
        todo.add('PERCENT-COMPLETE', '100')
        todo.add('COMPLETED', datetime.strptime(task['completedAt'], "%Y-%m-%dT%H:%M:%S.%f%z"))
        todo.add('LAST-MODIFIED', datetime.strptime(task['completedAt'], "%Y-%m-%dT%H:%M:%S.%f%z"))
    todo.add('COMMENT', task.get('notes', ''))
    if task.get('reminders', False):
        reminders = []
        for reminder in task['reminders']:
            try:
                reminders += [datetime.strptime(reminder['remindAt'], "%Y-%m-%dT%H:%M:%S.%f%z")]
            except ValueError: #Thank you for using different formats within the same file!
                try:
                    reminders += [datetime.strptime(reminder['remindAt'], "%Y-%m-%dT%H:%M:%S%z")]
                except:
                    logger.error('Could not parse reminder date for Task {}'.format(task['id']))
        logger.debug('Task {} has {} reminders. Not supported'.format(task['id'], len(reminders)))
    if task.get('comment', False):
        todo.add('description', task['comment'])
    if task.get('files', False):
        logger.error('There are files linked!')
    if parent is not None:
        todo.add('RELATED-TO', parent)
    todos.extend([todo])
    if task.get('subtasks', False):
        logger.debug('Task {} has {} subtasks'.format(task['id'], len(task['subtasks'])))
        for subtask in task['subtasks']:
            todos.extend(createVTODOs(subtask, parent=task['id']))
    return todos

if __name__ == '__main__':
    arguments = docopt(__doc__, version=VERSION)
    logger.warning('Reminders are not supported yet...')
    data = readFile(arguments['FILE'], arguments['--encoding'])
    logger.info('Found {} lists'.format(len(data)))
    out_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath( __file__ )), arguments['--output-path']))
    for list in data:
        ical, name = process(list)
        writeICSFiles(ical, name, out_path)
