import pika,sys

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

def send_pcep_exchange(parsed_results):
    channel.basic_publish(exchange='pcep-exchange',routing_key='pcep-key',body=parsed_results)


def channel_close():
    channel.close()


def create_broker():
    channel.exchange_declare(exchange='pcep-exchange',exchange_type='topic')

    #result = channel.queue_declare(queue='pcep_queue')
    #channel.queue_bind(exchange='pcep-exchange',queue='pcep_queue')


def main():
    create_broker()


if __name__ == '__main__':
    main()