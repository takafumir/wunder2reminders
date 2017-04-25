#! /usr/bin/env ruby

require 'json'
require 'securerandom'

wunderlist_backup = ARGV[0]
data = JSON.load( File.read(wunderlist_backup) )

def task_data(item)
  created_at = format_date(item['created_at'])
  task_data = <<"EOS"
BEGIN:VTODO
DTSTAMP:#{created_at}
SEQUENCE:0
SUMMARY:#{item['title']}
CREATED:#{created_at}
UID:#{SecureRandom.uuid.upcase}
EOS

  # include completed info if the task is completed
  if item['completed'] == true
    completed_at = format_date(item['completed_at'])
    completed_info = <<"EOS"
STATUS:COMPLETED
COMPLETED:#{completed_at}
PERCENT-COMPLETE:100
LAST-MODIFIED:#{completed_at}
EOS
    task_data += completed_info
  end

  task_data + "END:VTODO\n"
end

def format_date(date)
  date.gsub(/\.\d*Z\z/, 'Z').gsub(/[^\dTZ]/, '')
end

lists = data['data']['lists'].map{ |item| [item['id'], item['title']] }.to_h
lists.each do |list_id, list_title|
  tasks = data['data']['tasks'].select{ |item| item['list_id'] == list_id }.map{ |item| task_data(item) }.join
  tasks = "BEGIN:VCALENDAR\n" + tasks + "END:VCALENDAR"
  File.write("./reminders/#{list_title.gsub(/\//, ':')}.ics", tasks)
end

puts lists.values
