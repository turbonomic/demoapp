FROM locustio/locust

COPY comments.txt /home/locust
COPY run_locust.sh /home/locust/
COPY locustfile.py /home/locust/

EXPOSE 5557 5558 8089

ENTRYPOINT ["/home/locust/run_locust.sh"]
