pipeline {
    agent any

    parameters {
        string(name: 'DUT_IP', defaultValue: '192.168.102.76', description: 'GRL USB PD C2 Hardware IP')
        string(name: 'DUT_PORT', defaultValue: '5003', description: 'Web Application Port')
        booleanParam(name: 'HEADLESS', defaultValue: true, description: 'Run Playwright in headless mode')
        choice(name: 'TEST_SCOPE', choices: ['Smoke', 'Full', 'Smart'], description: 'Execution scope')
        string(name: 'PARALLEL_WORKERS', defaultValue: '2', description: 'pytest-xdist workers')
        string(name: 'RERUN_COUNT', defaultValue: '1', description: 'Number of retries for flaky failures')
    }

    environment {
        PYTHON = 'C:\\Users\\GRL\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
        DUT_IP = "${params.DUT_IP}"
        HEADLESS = "${params.HEADLESS}"
    }

    stages {
        stage('Code Quality') {
            steps {
                bat 'python -m ruff check .'
            }
        }

        stage('Execute USB PD C2 Tests') {
            steps {
                script {
                    def workerArgs = params.PARALLEL_WORKERS.toInteger() > 1 ? "-n ${params.PARALLEL_WORKERS} --dist=loadfile" : ""
                    def rerunArgs = params.RERUN_COUNT.toInteger() > 0 ? "--reruns ${params.RERUN_COUNT} --reruns-delay 2" : ""
                    def marker = params.TEST_SCOPE == 'Smoke' ? "-m smoke" : ""

                    bat """
                        python -m pytest -c Configurations\\pytest.ini Scripts\\TestCases ${marker} ${workerArgs} ${rerunArgs} --alluredir=allure-results -v
                    """
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'Reports/**, logs/**', allowEmptyArchive: true
        }
    }
}
