from string import Template
import os
import argparse

DEFUALT_IMAGE_TAG = 'latest'

dockerfile_temp = Template("""
                    FROM vmturbo/python-flask-grpc:latest
                    COPY cass_driver/ /cass_driver/
                    COPY $svc_name/ /$svc_name/
                    COPY entrypoint.sh.tmp /entrypoint.sh
                    RUN chmod 755 /entrypoint.sh
                    EXPOSE $svc_port
                    ENTRYPOINT ["/entrypoint.sh"]
                    """)

entrypoint_temp = Template("""#!/bin/bash
sleep 3
python $python_main_path &
while true; do sleep 3600; done
                    """)


def get_build_list(image_tag):
    return [
        {
            'img': 'vmturbo/twitter-cass-api:' + image_tag,
            'svc_name': 'http_server',
            'svc_port': '8699',
            'python_main_path': '/http_server/http_server.py',
        },
        {
            'img': 'vmturbo/twitter-cass-user:' + image_tag,
            'svc_name': 'user_service',
            'svc_port': '50051',
            'python_main_path': '/user_service/user_service_grpc.py',
        },
        {
            'img': 'vmturbo/twitter-cass-tweet:' + image_tag,
            'svc_name': 'tweet_service',
            'svc_port': '50052',
            'python_main_path': '/tweet_service/tweet_service_grpc.py',
        },
        {
            'img': 'vmturbo/twitter-cass-friend:' + image_tag,
            'svc_name': 'friend_service',
            'svc_port': '50053',
            'python_main_path': '/friend_service/friend_service_grpc.py',
        },
    ]


def docker_build(svc_name, svc_port, python_main_path, img):
    dockerfile = dockerfile_temp.substitute(svc_name=svc_name, svc_port=svc_port)
    entrypoint = entrypoint_temp.substitute(python_main_path=python_main_path)

    # Write to temp files: Dockerfile.tmp and entrypoint.tmp
    with open("Dockerfile.tmp", "w") as text_file:
        text_file.write(dockerfile)

    with open("entrypoint.sh.tmp", "w") as text_file:
        text_file.write(entrypoint)

    cmd = "docker build -t " + img + " -f Dockerfile.tmp ."
    print("=============================================================================")
    print(cmd)
    print("=============================================================================")
    os.system(cmd)
    return img


def docker_push(img):
    cmd = "docker push " + img
    print("=============================================================================")
    print(cmd)
    print("=============================================================================")
    os.system(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", help="push images to docker hub", action="store_true")
    parser.add_argument("--svc", help="service to build [http_server, user_service, tweet_service or friend_service]")
    parser.add_argument("--tag", help="tag of the docker images")
    args = parser.parse_args()

    push = args.push
    svc = args.svc
    tag = args.tag if args.tag else DEFUALT_IMAGE_TAG

    build_list = get_build_list(tag)

    for build in build_list:
        if svc and build['svc_name'] != svc:
            continue
        img = docker_build(**build)
        docker_push(img) if push else None
