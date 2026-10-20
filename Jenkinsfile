pipeline {
    agent any

    parameters {
        string(
            name: 'ANSIBLE_SERVER',
            defaultValue: '',
            description: 'Ansible control-server public IP or hostname'
        )
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('copy files to ansible server') {
            steps {
                script {
                    if (!(params.ANSIBLE_SERVER ==~ /[A-Za-z0-9][A-Za-z0-9.-]*/)) {
                        error('Supply a valid Ansible server IP address or hostname.')
                    }

                    env.CONTROL_HOST = params.ANSIBLE_SERVER
                }

                withCredentials([
                    file(
                        credentialsId: 'ansible-server-known-hosts',
                        variable: 'CONTROL_KNOWN_HOSTS'
                    )
                ]) {
                    sshagent(['ansible-server-key']) {
                        sh '''
                            set -eu

                            git rev-parse HEAD > source-revision.txt

                            scp \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                ansible/ansible.cfg \
                                ansible/my-playbook.yaml \
                                ansible/inventory_aws_ec2.yaml \
                                ansible/requirements.txt \
                                ansible/requirements.yml \
                                scripts/check-inventory.py \
                                scripts/check-results.py \
                                source-revision.txt \
                                "root@$CONTROL_HOST:/root/"
                        '''

                        withCredentials([
                            sshUserPrivateKey(
                                credentialsId: 'ec2-server-key',
                                keyFileVariable: 'EC2_KEY'
                            )
                        ]) {
                            script {
                                env.EC2_KEY_TRANSFER_STARTED = 'true'
                            }

                            sh '''
                                set +x
                                set -eu

                                ssh \
                                    -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "root@$CONTROL_HOST" \
                                    'umask 077; cat > /root/ssh-key.pem' \
                                    < "$EC2_KEY"
                            '''
                        }
                    }
                }
            }
        }

        stage('execute ansible playbook') {
            steps {
                script {
                    withCredentials([
                        sshUserPrivateKey(
                            credentialsId: 'ansible-server-key',
                            keyFileVariable: 'CONTROL_KEY',
                            usernameVariable: 'CONTROL_USER',
                            passphraseVariable: 'CONTROL_PASSPHRASE'
                        ),
                        file(
                            credentialsId: 'ansible-server-known-hosts',
                            variable: 'CONTROL_KNOWN_HOSTS'
                        )
                    ]) {
                        if (env.CONTROL_USER != 'root') {
                            error('The Ansible control credential must use root.')
                        }

                        def remote = [
                            name: 'ansible-server',
                            host: params.ANSIBLE_SERVER,
                            user: env.CONTROL_USER,
                            identityFile: env.CONTROL_KEY,
                            passphrase: env.CONTROL_PASSPHRASE,
                            knownHosts: env.CONTROL_KNOWN_HOSTS,
                            allowAnyHosts: false
                        ]

                        sshScript(
                            remote: remote,
                            script: 'prepare-ansible-server.sh'
                        )

                        sshCommand(
                            remote: remote,
                            command: '''bash -lc '
                                set -euo pipefail
                                cd /root

                                export PATH=/opt/ansible-project/bin:$PATH
                                export ANSIBLE_CONFIG=/root/ansible.cfg
                                export ANSIBLE_NOCOLOR=1
                                export ANSIBLE_STDOUT_CALLBACK=default

                                rm -f project-verification.json

                                ansible-inventory --list > project-inventory.json

                                python check-inventory.py project-inventory.json

                                ansible-playbook my-playbook.yaml |
                                    tee playbook-first.log

                                ansible-playbook my-playbook.yaml |
                                    tee playbook-second.log

                                python check-results.py
                            ' '''
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (env.EC2_KEY_TRANSFER_STARTED == 'true') {
                    withCredentials([
                        file(
                            credentialsId: 'ansible-server-known-hosts',
                            variable: 'CONTROL_KNOWN_HOSTS'
                        )
                    ]) {
                        sshagent(['ansible-server-key']) {
                            sh '''
                                set -eu

                                ssh \
                                    -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "root@$CONTROL_HOST" \
                                    'rm -f /root/ssh-key.pem'
                            '''
                        }
                    }
                }
            }
        }
    }
}
