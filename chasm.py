import paramiko
import subprocess
import time

hostname = '服务器ip'
username = '用户名'
password = '密码'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)
stdin, stdout, stderr = ssh.exec_command('echo "SSH connection successful"')
print(stdout.read().decode('utf-8'))
# 检验docker
def verify_docker():
    # 检查是否已安装Docker
    stdin, stdout, stderr = ssh.exec_command('docker -v')
    docker_installed = 'Docker version' in stdout.read().decode('utf-8')

    if not docker_installed:
        # 下载并安装Docker
        stdin, stdout, stderr = ssh.exec_command('curl -fsSL https://get.docker.com -o get-docker.sh')
        stdin, stdout, stderr = ssh.exec_command('sudo sh get-docker.sh')
        print(stdout.read().decode('utf-8'))
        time.time(10*1000)

    stdin, stdout, stderr = ssh.exec_command('sudo systemctl start docker')

    stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active docker')
    docker_active = stdout.read().decode('utf-8').strip() == 'active'

    if docker_active:
        print('Docker已成功安装并启动。')
    else:
        print('无法启动Docker。')
# 安装节点
def node():
    verify_docker()
    stdin, stdout, stderr = ssh.exec_command('if [ ! -d /opt/chasm ]; then echo "not_exists"; fi')
    folder_exists = stdout.read().decode('utf-8').strip() != 'not_exists'

    if not folder_exists:
        # 创建文件夹
        stdin, stdout, stderr = ssh.exec_command('mkdir /opt/chasm')
        print('文件夹已成功创建。')
    else:
        print('文件夹已存在，无需创建。')
    # 创建文件
    stdin, stdout, stderr = ssh.exec_command('cd /opt/chasm && ls -l')
    print(stdout.read().decode('utf-8'))
    userInput_touch = input("请输入你要创建的文件，请以.env结尾，例如1.env,2.env:")
    userInput_port = int(input("请输入端口号（建议3001-10000之间）："))
    stdin, stdout, stderr = ssh.exec_command('docker ps -a')
    print(stdout.read().decode('utf-8'))
    SCOUT_NAME = input("SCOUT_NAME(节点名称任意即可，但不可与已有的重复)：")
    SCOUT_UID = input("SCOUT_UID：")
    WEBHOOK_API_KEY = input("WEBHOOK_API_KEY：")
    GROQ_API_KEY = input("GROQ_API_KEY：")
    # 向env文件并写入内容
    env_content = f'''
PORT={userInput_port}
LOGGER_LEVEL=debug

# Chasm
ORCHESTRATOR_URL=https://orchestrator.chasm.net
SCOUT_NAME={SCOUT_NAME}
SCOUT_UID={SCOUT_UID}
WEBHOOK_API_KEY={WEBHOOK_API_KEY}
# Scout Webhook Url, update based on your server's IP and Port
# e.g. http://123.123.123.123:3001/
WEBHOOK_URL=http://{hostname}:{userInput_port}/

# Chosen Provider (groq, openai)
PROVIDERS=groq
MODEL=gemma2-9b-it
GROQ_API_KEY={GROQ_API_KEY}

# Optional
OPENROUTER_API_KEY=
OPENAI_API_KEY=
'''
    stdin, stdout, stderr = ssh.exec_command(f'echo "{env_content}" > /opt/chasm/{userInput_touch}')

    # 拉取Docker镜像
    stdin, stdout, stderr = ssh.exec_command('docker pull johnsonchasm/chasm-scout')
    print(stdout.read().decode('utf-8'))

    # 启动Docker容器
    command = f'docker run -d --restart=always --env-file /opt/chasm/{userInput_touch} -p {userInput_port}:{userInput_port} --name {SCOUT_NAME} johnsonchasm/chasm-scout'
    stdin, stdout, stderr = ssh.exec_command(command)

    # 打印命令执行结果
    print(stdout.read().decode('utf-8'))


# 查询日志
def node_logs():
    stdin, stdout, stderr = ssh.exec_command('docker ps -a')
    print(stdout.read().decode('utf-8'))
    userInput = input("请输入你要查询节点名称：")
    stdin, stdout, stderr = ssh.exec_command(f'docker logs -f {userInput}')
    print(stdout.read().decode('utf-8'))
# 查询状态
def node_state():
    stdin, stdout, stderr = ssh.exec_command('docker ps -a')
    print(stdout.read().decode('utf-8'))
    userInput = input("请输入你要查询节点名称：")
    command =f'docker stats {userInput}'
    process = subprocess.Popen(command, shell=True)
    input("按下任意键停止 docker stats scout...")
    process.terminate()
# 查询llm功能
def node_cat_llm():
    stdin, stdout, stderr = ssh.exec_command('cd /opt/chasm && ls -l')
    print(stdout.read().decode('utf-8'))
    userInput = input("请输入你要查看llm的env名称例如.env 1.env 2.env：")
    stdin, stdout, stderr = ssh.exec_command(
        'export $(cat /opt/chasm/' + userInput + ' | xargs) && curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $WEBHOOK_API_KEY" -d \'{"body":"{\\"model\\":\\"gemma-7b-it\\",\\"messages\\":[{\\"role\\":\\"system\\",\\"content\\":\\"You are a helpful assistant.\\"}]}"}\' $WEBHOOK_URL')
    print(stdout.read().decode('utf-8'))
# 卸载节点
def delete_node():
    stdin, stdout, stderr = ssh.exec_command('docker ps -a')
    print(stdout.read().decode('utf-8'))
    userInput = input("请输入你要卸载的节点名称：")
    stdin, stdout, stderr = ssh.exec_command(f'docker stop {userInput}')
    stdin, stdout, stderr = ssh.exec_command(f'docker rm {userInput}')
def main_menu():
    while True:
        print('''
        =========脚本由anni创作，免费开源===========
        1. 安装节点
        2. 查询日志
        3. 卸载节点
        4. 查询状态
        5. 退出
        注意：多个请注意端口号和文件需改动
        ===========================================
        ''')
        userInput = int(input("请输入你要执行的步骤序号："))
        if userInput == 1:
            node()
        elif userInput == 2:
            node_logs()
        elif userInput == 3:
            delete_node()
        elif userInput == 4:
            node_state()
        elif userInput == 5:
            ssh.close()
            break
        else:
            print("您输入的有误，请重新输入：")


main_menu()

