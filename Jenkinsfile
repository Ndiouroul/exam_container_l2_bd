pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "dit-library"
        DOCKER_BUILDKIT = "1"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Installation Docker Compose') {
            steps {
                sh '''
                    # Si docker compose est absent, on l'installe
                    if ! command -v docker compose &> /dev/null; then
                        echo "Installation de docker compose..."
                        curl -L "https://github.com/docker/compose/releases/latest/download/docker compose-$(uname -s)-$(uname -m)" -o docker compose
                        chmod +x docker compose
                        # On déplace le binaire
                        sudo mv docker compose /usr/local/bin/docker compose
                    fi
                '''
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
                sh 'docker compose build'
            }
        }

        stage('Tests des microservices') {
            steps {
                sh '''
                    docker compose up -d postgres
                    sleep 8
                    docker compose up -d books-service users-service loans-service
                    sleep 8

                    echo "-- Test de santé des services --"
                    curl -f http://localhost:8001/health
                    curl -f http://localhost:8002/health
                    curl -f http://localhost:8003/health
                '''
            }
        }

        stage('Déploiement') {
            steps {
                sh '''
                    docker compose up -d
                    docker compose ps
                '''
            }
        }

        stage('Vérification post-déploiement') {
            steps {
                sh 'sleep 5 && curl -f http://localhost:3000'
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès."
        }
        failure {
            echo "❌ Échec du pipeline."
            sh 'docker compose down || true'
        }
        always {
            sh 'docker system prune -f || true'
        }
    }
}
