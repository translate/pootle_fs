import django_rq
import datetime


def func():
    print "Boom!"


scheduler = django_rq.get_scheduler('default')
scheduler.schedule(datetime.datetime.utcnow(),
                   func,
                   interval=5)
