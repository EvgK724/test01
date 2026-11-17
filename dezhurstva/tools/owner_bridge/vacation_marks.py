"""Public approved-only vacation marks. No raw wishes, free text or private causes."""
import datetime

def validate(draft):
 marks=draft.get('marks')
 if type(marks)is not list or len(marks)>372:raise ValueError('VACATION_MARKS_REQUIRED')
 order=draft['order'];month=draft['month'];seen=set();last=None
 for m in marks:
  if type(m)is not dict or set(m)!={'who','from','to','label'} or m['label']!='Отпуск' or type(m['who'])is not str or m['who']not in order:raise ValueError('VACATION_MARK_SCHEMA')
  try:
   a=datetime.date.fromisoformat(m['from']);b=datetime.date.fromisoformat(m['to'])
  except (ValueError,TypeError):raise ValueError('VACATION_MARK_DATE')
  if a.isoformat()!=m['from'] or b.isoformat()!=m['to'] or m['from'][:7]!=month or m['to'][:7]!=month or a>b:raise ValueError('VACATION_MARK_DATE')
  key=(order.index(m['who']),a)
  if last and key<=last[0]:raise ValueError('VACATION_MARK_ORDER')
  if last and last[1]['who']==m['who'] and a<=datetime.date.fromisoformat(last[1]['to'])+datetime.timedelta(days=1):raise ValueError('VACATION_MARK_NONCANONICAL')
  last=(key,m)
  while a<=b:
   date=a.isoformat();pair=(m['who'],date)
   if pair in seen or m['who'] in draft['duty'].get(date,[]):raise ValueError('VACATION_DUTY_CONFLICT')
   seen.add(pair);a+=datetime.timedelta(days=1)
 return marks
