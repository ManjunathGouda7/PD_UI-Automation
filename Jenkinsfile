pipeline {
    // Needs a Windows agent on the bench PC that runs the GRL software and is wired to the tester.
    agent { label 'grl-pd-bench' }

    options {
        timeout(time: 90, unit: 'MINUTES')
        disableConcurrentBuilds()   // one physical tester: never run two builds against it at once
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    parameters {
        string(name: 'BASE_URL', defaultValue: 'http://localhost:5003', description: 'GRL C2 software host (version page is auto-resolved)')
        string(name: 'DUT_IP', defaultValue: '192.168.255.1', description: 'Tester IP used by connect tests')
        choice(name: 'TEST_SCOPE', choices: ['smoke', 'full', 'api', 'smart'], description: 'Execution scope')
        booleanParam(name: 'ALLOW_HW_ACTIONS', defaultValue: false, description: 'Run tests that change tester state')
        booleanParam(name: 'STRICT_HARDWARE', defaultValue: false, description: 'Fail (not skip) when no tester is connected')
        string(name: 'RERUN_COUNT', defaultValue: '1', description: 'Reruns for failed tests')
    }

    environment {
        BASE_URL = "${params.BASE_URL}"
        DUT_IP = "${params.DUT_IP}"
        HEADLESS = 'true'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Setup') {
            steps {
                bat 'python -m pip install -q -r requirements.txt'
                bat 'python -m playwright install chromium'
            }
        }

        stage('Code Quality') {
            steps {
                bat 'python -m ruff check .'
            }
        }

        stage('Framework Unit Tests') {
            steps {
                bat 'python -m pytest tests/unit -q --junitxml=Reports/unit-junit.xml'
            }
        }

        stage('Locator Health') {
            steps {
                // Read-only: fails fast if a new GRL build changed the UI the page objects rely on
                bat 'python tools/locator_check.py'
            }
        }

        stage('Tests') {
            steps {
                script {
                    def scope = params.TEST_SCOPE == 'smart' ? '--smart' : "--mode ${params.TEST_SCOPE}"
                    def hw = params.ALLOW_HW_ACTIONS ? '--allow-hw-actions' : ''
                    def strict = params.STRICT_HARDWARE ? '--strict-hardware' : ''
                    bat "python run.py ${scope} ${hw} ${strict} --retries ${params.RERUN_COUNT} --allure --headless"
                }
            }
        }
    }

    post {
        always {
            bat 'python tools/traceability.py'
            junit allowEmptyResults: true, testResults: 'Reports/junit.xml, Reports/unit-junit.xml'
            archiveArtifacts artifacts: 'Reports/**, logs/**', allowEmptyArchive: true
        }
    }
}
