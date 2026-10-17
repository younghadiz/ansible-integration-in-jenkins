pipeline {
    agent any

    parameters {
        string(
            name: 'ANSIBLE_SERVER',
            defaultValue: '',
            description: 'Ansible control server IP address or hostname'
        )
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('copy files to ansible server') {
            steps {
                script {
                    if (!(params.ANSIBLE_SERVER ==~ /[A-Za-z0-9][A-Za-z0-9.-]*/)) {
                        error('Supply a valid Ansible server IP address or hostname.')
                    }
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
                            scp -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                ansible/ansible.cfg \
                                ansible/my-playbook.yaml \
                                ansible/inventory_aws_ec2.yaml \
                                ansible/requirements.txt \
                                ansible/requirements.yml \
                                "root@$ANSIBLE_SERVER:/root/"
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
                                scp -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "$EC2_KEY" "root@$ANSIBLE_SERVER:/root/ssh-key.pem"
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
                            usernameVariable: 'CONTROL_USER'
                        ),
                        file(
                            credentialsId: 'ansible-server-known-hosts',
                            variable: 'CONTROL_KNOWN_HOSTS'
                        )
                    ]) {
                        if (env.CONTROL_USER != 'root') {
                            error('The Ansible control-server credential must use root.')
                        }

                        def remote = [
                            name: 'ansible-server',
                            host: params.ANSIBLE_SERVER,
                            user: env.CONTROL_USER,
                            identityFile: env.CONTROL_KEY,
                            knownHosts: env.CONTROL_KNOWN_HOSTS,
                            allowAnyHosts: false
                        ]

                        sshScript remote: remote,
                            script: 'prepare-ansible-server.sh'

                        sshCommand remote: remote,
                            command: 'cd /root && /opt/ansible-project/bin/ansible-playbook my-playbook.yaml'
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
                                ssh -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    -o UserKnownHostsFile="$CONTROL_KNOWN_HOSTS" \
                                    "root@$ANSIBLE_SERVER" \
                                    'rm -f /root/ssh-key.pem'
                            '''
                        }
                    }
                }
            }
        }
    }
}
