pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "dit-library"
        DOCKER_BUILDKIT = "0"
        COMPOSE_DOCKER_CLI_BUILD = "0"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Vérification Docker Compose') {
            steps {
                script {
                    if (sh(script: 'docker compose version > /dev/null 2>&1', returnStatus: true) == 0) {
                        env.COMPOSE_CMD = 'docker compose'
                    } else if (sh(script: 'command -v docker-compose > /dev/null 2>&1', returnStatus: true) == 0) {
                        env.COMPOSE_CMD = 'docker-compose'
                    } else {
                        error("Ni 'docker compose' (v2) ni 'docker-compose' (v1) ne sont disponibles sur cet agent.")
                    }
                    echo "✅ Commande Compose détectée : ${env.COMPOSE_CMD}"
                }
            }
        }

        stage('Nettoyage préalable') {
            steps {
                sh "${env.COMPOSE_CMD} down --remove-orphans || true"
            }
        }

        stage('Checkout') {
            steps {
                echo "Récupération du code depuis GitHub"
                checkout scm
            }
        }

        stage('Lint & Vérifications') {
            parallel {
                stage('Backend - vérification syntaxe Python') {
                    steps {
                        sh '''
                            for service in books-service users-service loans-service; do
                                echo "-- Vérification $service --"
                                python3 -m py_compile backend/$service/app/*.py
                            done
                        '''
                    }
                }
                stage('Frontend - installation & build') {
                    steps {
                        dir('frontend') {
                            sh 'npm install'
                            sh 'npm run build'
                        }
                    }
                }
            }
        }

        stage('Build des images Docker') {
            steps {
                sh "${env.COMPOSE_CMD} build"
            }
        }

        stage('Tests des microservices') {
            steps {
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe']) {
                    sh """
                        ${env.COMPOSE_CMD} up -d postgres
                        sleep 15
                        ${env.COMPOSE_CMD} up -d books-service users-service loans-service
                        sleep 15
                    """
                    script {
                        try {
                            sh """
                                echo "-- Test de santé des services (via réseau Docker interne) --"
                                docker exec dit-books-service curl -f http://localhost:8001/health
                                docker exec dit-users-service curl -f http://localhost:8002/health
                                docker exec dit-loans-service curl -f http://localhost:8003/health
                            """
                        } catch (err) {
                            echo "❌ Échec du health check — logs des conteneurs :"
                            sh "docker logs dit-books-service --tail 50 || true"
                            sh "docker logs dit-users-service --tail 50 || true"
                            sh "docker logs dit-loans-service --tail 50 || true"
                            sh "docker logs dit-postgres --tail 50 || true"
                            error("Health check failed — voir logs ci-dessus")
                        }
                    }
                }
            }
        }

        stage('Déploiement') {
            steps {
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe']) {
                    sh """
                        ${env.COMPOSE_CMD} up -d
                        ${env.COMPOSE_CMD} ps
                    """
                }
            }
        }

        stage('Vérification post-déploiement') {
            steps {
                sh 'sleep 5 && docker exec dit-frontend wget -qO- http://localhost:80'
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès. Les conteneurs restent actifs en arrière-plan."
        }
        failure {
            echo "❌ Échec du pipeline."
            sh "${env.COMPOSE_CMD ?: 'docker-compose'} down --remove-orphans || true"
        }
        always {
            sh 'docker system prune -f || true'
        }
    }
}
