import socket
import base64
import os
import time
import threading
import json
import mimetypes
import shutil
#connect to SMTP
def connectToSmtp(ip, port):
    sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sender.connect((ip, port))
    responseFromServer = sender.recv(1024)
    print(responseFromServer)
    return sender

# send to server , then receive response from server
def sendAndResponse(sender, command):
    command += '\r\n'
    sender.sendall(command.encode())
    responseFromServer = sender.recv(1024)
    print(responseFromServer.decode())


# dùng để lưu trữ các thông tin cần thiết khi gửi 1 mail
class emailStored:
    def __init__(self,toMailInput,ccInput,bccInput,subjectInput,bodyContentInput, attachmentPaths):
        self.toMail = toMailInput
        self.cc = ccInput
        self.bcc = bccInput
        self.rcpt = list(set( self.toMail+ self.cc + self.bcc))  # Remove duplicates
        self.subject = subjectInput
        self.bodyContent = bodyContentInput
        self.attachmentPaths = attachmentPaths

# Nhập các thông tin để gửi mail
def inputEmailFromKeyBoard():
    attachmentPaths = []
    toMailInput = input("To: ").split()
    ccInput = input("CC: ").split()
    bccInput = input("BCC: ").split()
    #sửa ngày 14/12
    flag = False
    while not toMailInput and not ccInput and not bccInput:
        try:    
            choice = int(input("Bạn cần nhập ít nhất một email để gửi đến(Nhấn 1 để tiếp tục hoặc 0 để thoát)"))
            if choice == 0:
                flag = True
                break
            elif choice == 1:
                toMailInput = input("To: ").split()
                ccInput = input("CC: ").split()
                bccInput = input("BCC: ").split()
            else:
                print("Lựa chọn không hợp lệ")
        except ValueError:
            print("Lỗi: Bạn phải nhập một số nguyên. Vui lòng thử lại.")        
    if(flag == True):
        return False
    subjectInput = input("Subject: ")
    bodyContentInput = ""
    print("Content(press enter twice to finish):")
    while True:
        line = input()
        if line.strip() == "":
            break
        bodyContentInput += "\n" + line + "\n"
    while True:
        checkFile = input("Có gửi kèm file (1. có, 2. không): ")
        if checkFile in ['1', '2']:
            break
        else:
            print("Nhập đúng định dạng.\r\n")

    if checkFile == "1":
        while True:
            strFile = input("Số lượng file muốn gửi: ")
            try:
                intFile = int(strFile)
                break
            except Exception as e:
                print("Vui lòng nhập số nguyên.\r\n")
        i = 1
        while i <= intFile:
            pathFile = input(f"Cho biết đường dẫn file thứ {i}: ./")
            attachmentPaths.append(pathFile)
            i += 1
        

   # tạo một cái Menu ở đây để gọi hàm gửi file, rồi thêm thông tin của file vào cấu trúc email để lưu lại
    email = emailStored(toMailInput,ccInput,bccInput,subjectInput,bodyContentInput, attachmentPaths)
    
    return email


# Gửi các thông tin cần thiết và nội dung mail đến server 
def sendEmail(smtpIp,smtpPort,user, userMail,email):
    boundary = "------------boundary"
    count = 0
    sender = connectToSmtp(smtpIp, smtpPort)

    #gửi lời chào kết nối đến server và nhận phản hồi từ server
    sendAndResponse(sender, 'EHLO')

    # gửi thông tin của mail user và nhận phản hồi từ server
    mailFromCommand = "MAIL FROM: <{}>".format(userMail)
    sendAndResponse(sender, mailFromCommand)

    # gửi các mail nhận mail từ user và nhạn phản hồi từ server
    for rcpt in email.rcpt:
        rcptToCommand = "RCPT TO: <{}>".format(rcpt)
        sendAndResponse(sender, rcptToCommand)

    #gửi lệnh DATA để bắt đầu và nhận phản hồi từ server
    sendAndResponse(sender, 'DATA')

    # Thêm dấu vào để dịnh dạng mail1, mail2,... mailn
    storedTo = ', '.join(email.toMail)
    # Gửi danh sách to mail
    sender.sendall("To: {}\r\n".format(storedTo).encode())


    storedCc = ', '.join(email.cc)
    # Gửi danh sách cc
    sender.sendall("Cc: {}\r\n".format(storedCc).encode())

    # Gửi mail user và tên user
    storedFrom = "From: {} <{}>\r\n".format(user, userMail)
    sender.sendall(storedFrom.encode())
    '''
    # Gửi subject
    subjectAfterEncode = '=?UTF-8?B?{}?=\r\n'.format(base64.b64encode(email.subject.encode()).decode()) ## Này
    sender.sendall("Subject: {}\r\n".format(subjectAfterEncode).encode())
    
    # Gửi nội dung1
    ##bodyContentAfterEncode = '=?UTF-8?B?{}?=\r\n'.format(base64.b64encode(email.bodyContent.encode()).decode()) # Này
    sender.sendall("{}\r\n".format(email.bodyContent).encode())
    '''
    numSentFile = sendFile(sender, email.subject , email.bodyContent ,email.attachmentPaths , boundary, count)
    print(f'Đã gửi {numSentFile} file thành công.')
    
    # Gửi dấu '.' để kết thúc nội dung
    #sender.sendall('\r\n'.encode()) #NEW CHANGE

    responseFromServer = sender.recv(1024)
    print(responseFromServer.decode())

    # Gửi lệnh "QUIT" để dừng kết nối đến server và nhận phản hồi
    sendAndResponse(sender, 'QUIT')

    # Đóng kết nối
    sender.close()

    print("\nĐã gửi mail thành cônng\n\n")


#-----------mới sửa------#
#hàm xử lí định dạng file
#hàm mới sửa
def solveFormatFile(fileName):
    #tailFile = os.path.splitext(fileName)[1][1:]
    #hàm guess_type xác định nội dung và loại mã hoá tệp
    """
    vd: jpg:  image/jpeg
        txt:  text/plain
        
    """
    contentType, encoding = mimetypes.guess_type(fileName)
    # định dạng header file tập tin
    if contentType is not None:
        if fileName.endswith("txt"):
            headerFile = f'Content-Type: {contentType}; charset=UTF-8; name="{fileName}"'
        else:
            headerFile = f'Content-Type: {contentType}; name="{fileName}"'
        headerFile += "\r\n"
    else:
        headerFile=f''
    
    return headerFile

#giải quyết vấn đề gửi file
def solveFile(attachmentPath,server, boundary, count):
    #lấy dường dẫn file hiện tại nhé
    current_directory = os.path.dirname(os.path.abspath(__file__))
    #nối thành đường dẫn cần đến để đọc file
    dpath = os.path.join(current_directory, attachmentPath)
    #lấy tên file
    fileName = os.path.basename(dpath)
    #lấy kích cỡ file
    try:
        fileSize = round(os.path.getsize(dpath)/(1024**2), 4)
    except Exception as e:
        print(f"File {fileName} không tồn tại")
        return 0
    #xử lí nếu file > 3mb thoát khỏi hàm 
    if fileSize > 3:
        print(f'File {fileName}: {fileSize} MB. Khong the gui file lon hon 3 MB')
        return count
    #nếu tới được bước này thì xử lí file
    #email_data += f'--{boundary}\r\nContent-Type: image/jpeg; filename="{attachment_path}"'
    #tạm thời chưa xử lí được định dạng file
    email_data = f'--{boundary}\r\n'
    email_data += solveFormatFile(fileName)
    email_data += f'Content-Disposition: attachment; filename="{fileName}"\r\n'
    email_data += 'Content-Transfer-Encoding: base64\r\n\r\n'
    server.sendall(email_data.encode())

    # Đọc và thêm nội dung file vào email_data
    CHUNK_SIZE = 128
    try:
        with open(dpath, 'rb') as attachment:
            while True:
                chunk = attachment.read(CHUNK_SIZE)
                if not chunk:
                    #server.sendall("==".encode())
                    break
                email_data = base64.b64encode(chunk)
                email_data = email_data + b"=\r\n"
                #print(email_data + "\r\n")
                server.sendall(email_data)
    except Exception as e:
        print(f"Outer exception: {str(e)}")

    return 1

#hàm xử lí phần data của file
def sendFile(server, subject, bodyContent, attachmentPaths, boundary, count):
    # Đọc và thêm nội dung file vào email_data
    current_directory = os.path.dirname(os.path.abspath(__file__))
    email_data = f'Subject: {subject}\r\n'
    #email_data += f'To: {toEmail}\r\n'
    #email_data += f'From: {fromEmail}\r\n'
    email_data += 'MIME-Version: 1.0\r\n'
    email_data += 'Content-Type: multipart/mixed; boundary={}\r\n\r\n'.format(boundary)
    email_data += f'--{boundary}\r\nContent-Type: text/plain; charset=UTF-8; format=flowed\r\n'
    email_data += f'Content-Transfer-Encoding: 7bit'
    email_data += f'\r\n{bodyContent}\r\n'
    server.sendall(email_data.encode())
    
    for attachmentPath in attachmentPaths:
        count += solveFile(attachmentPath,server, boundary, count)

    email_data = '\r\n--{}--\r\n.\r\n'.format(boundary)
    server.sendall(email_data.encode())

    return count

#-------------------------------------------------------------------------------------------#
# yêu cầu 3: 
#-------------------------------------------------------------------------------------------#
#hàm nhận mail bằng giao thưc pop3 
def getMail(POP3Server, POP3Port, userName, outputFolder, configFilePath):
    
    #tạo socket kết nối đến máy chủ pop3 
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((POP3Server, POP3Port))

    #nhận và hiện thị phản hồi từ máy chủ 
    response = clientSocket.recv(1024)
    # print(response.decode())

    #gửi lệnh USER để xác định tên người dùng 
    userCommand = "USER {}\r\n".format(userName)
    clientSocket.sendall(userCommand.encode())
    response = clientSocket.recv(1024)
    # print(response.decode())

    #gửi lệnh LIST để lấy danh sách thư mục 
    listCommand = "LIST\r\n"
    clientSocket.sendall(listCommand.encode())
    response = clientSocket.recv(1024)
    # print(response.decode())

    # gửi lệnh UIDL để kiểm tra các mail chưa được tải về 
    uidlCommand = "UIDL\r\n"
    clientSocket.sendall(uidlCommand.encode())
    response = clientSocket.recv(1024)
    # print(response.decode())

    #xử lí chuỗi sau khi gửi mã UIDL để nhận được danh sách các mail chưa được tải về 
    uidList = response.decode().split('\r\n')[1:-2]
    #chú ý ta lấy từ dòng 1 -> dòng -2(là dòng thứ 2 đếm từ cuối lên)
    """
    ví dụ khi ta gọi 1 lệnh UIDL ta sẽ có các dòng tương ứng như sau 
    +OK
    1 20231206103329903.msg
    2 29213194124912412.msg
    .
    """
    for mailNumber in uidList:
        if not isCodeInFile(str(mailNumber.split()[1]), configFilePath):
            addCodeToFile(str(mailNumber.split()[1]), configFilePath)
            saveMail(clientSocket, int(mailNumber.split()[0]), mailNumber.split()[1], outputFolder)
    print("bạn đã cập nhật mail mới nhất")

    # Gửi lệnh QUIT và đóng kết nối
    quitCommand = "QUIT\r\n"
    clientSocket.sendall(quitCommand.encode())
    response = clientSocket.recv(1024)
    # print(response.decode())
    
    #giải phóng socket 
    clientSocket.close()
#-------------------------------------------------------------------------------------------#

def receiveData(client):
    data = b""
    try:
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\r\n" in data:
                break
    except Exception as e:
        print(f"Error occurred while receiving data: {e}")
    return data
#-------------------------------------------------------------------------------------------#   

def saveMail(client, mailNumber, uniqueMailName, outputFolder):
    """đây là hàm tải mail từ MailBoxServer về MailBoxClient"""
    client.sendall("RETR {}\r\n".format(mailNumber).encode())
    response = receiveData(client)

    if response.startswith(b"-ERR"):
        print("Error retrieving mail {}: {}".format(mailNumber, response.decode()).encode())
        return

    responseString = response.decode('utf-8', errors='ignore')

    if not os.path.exists(outputFolder):
        # Nếu không tồn tại, tạo thư mục mới
        os.makedirs(outputFolder)

    mailFileName = os.path.join(outputFolder, "{}".format(uniqueMailName))
    with open(mailFileName, 'w', encoding='utf-8', newline='') as file:
        while True:
            buffer = responseString[:4096]
            if not buffer:
                break
            responseString = responseString[4096:]
            #print("buffer", buffer)
            file.write(buffer)

            # Kiểm tra xem có đạt đến điều kiện kết thúc email không
            #
            if '--------------boundary--\r\n.' in buffer:
                break

            # Kiểm tra xem có dữ liệu thêm hay không
            additional_data = receiveData(client)
            if not additional_data or additional_data.startswith(b"-ERR"):
                break
            responseString += additional_data.decode('utf-8', errors='ignore')
            # print("response", responseString)


        # in thêm 1 số thông tin để đảm bảo mail tải xuống là hoàn chỉnh 

    # print("Mail saved to: {}".format(mailFileName))
#-------------------------------------------------------------------------------------------#

def listEmailsInFolder(folderPath):
    """Liệt kê danh sách các email có trong một thư mục."""
    emailList = []

    # Kiểm tra xem đường dẫn thư mục có tồn tại không
    if os.path.exists(folderPath) and os.path.isdir(folderPath):
        # Lặp qua tất cả các tệp tin trong thư mục
        for filename in os.listdir(folderPath):
            # Kiểm tra nếu là tệp tin và có phần mở rộng là '.msg' (hoặc thay đổi theo định dạng email của bạn)
            # if os.path.isfile(os.path.join(folderPath, filename)) and filename.lower().endswith('.msg'): #NEW FIX DUONG HUY
                emailList.append(filename)

    return emailList
#-------------------------------------------------------------------------------------------# 
def displaySelectedEmail(path):
    # Liệt kê danh sách email trong thư mục
    folder = [" ","Inbox","Project","Important","Work","Spam"]
    print("Đây là danh sách các folder trong mailbox của bạn:")
    print("1. {}\n2. {}\n3. {}\n4. {}\n5. {}".format(folder[1],folder[2],folder[3],folder[4],folder[5]))
    choice = input("Bạn muốn xem email trong folder nào(Nhấn enter để thoát ra ngoài):")
    if(choice == ""):
        return
    pathUnRead = ''
    pathRead = ''
    ## Này xem thử cấu hình vào config được không
    if(choice == '1'):
        pathUnRead = path
        pathRead = pathUnRead.replace("unread", "read")
    elif(choice == '2'):
        pathUnRead = path.replace("Inbox", "Project")
        pathRead = pathUnRead.replace("unread", "read")
    elif(choice == '3'):
        pathUnRead = path.replace("Inbox", "Important")
        pathRead = pathUnRead.replace("unread", "read")
    elif(choice == '4'):
        pathUnRead = path.replace("Inbox", "Work")
        pathRead = pathUnRead.replace("unread", "read")
    elif(choice == '5'):
        pathUnRead = path.replace("Inbox", "Spam")
        pathRead = pathUnRead.replace("unread", "read")
    ## Này xem thử cấu hình vào config được không
    else:
        print("Lựa chọn không hợp lệ.\n")

    ## Lấy danh sách email trong folder
    readEmailList = listEmailsInFolder(pathRead)
    unReadEmailList = listEmailsInFolder(pathUnRead)
    readIndex = 0
    unReadIndex = 0

    if not readEmailList and not unReadEmailList:
        print("Không có email nào trong thư mục.")
        return
    
    # Hiển thị danh sách email để người dùng chọn
    print("Đây là danh sách email trong {} folder:".format(folder[int(choice)]))
    readIndex, unReadIndex = DisplayListEmail(pathRead,pathUnRead)
    selected_index = 0
    flag = False

    while selected_index == 0:  
        while (selected_index == 0):
            selected_index = input("\nBạn muốn đọc Email thứ mấy (hoặc nhấn enter để thoát ra ngoài,hoặc nhấn 0 để xem lại danh sách email):")
            if(selected_index == ""):
                flag = True
                break
            selected_index = int(selected_index)
            if(selected_index == 0):
                print("Đây là danh sách email trong {} folder:".format(folder[int(choice)]))
                readIndex, unReadIndex = DisplayListEmail(pathRead,pathUnRead)

        if(flag == True):
            print("Thoát chương trình.")
            break
        
        ## Nếu email chọn nằm trong folder đã đọc
        if 0 < selected_index < readIndex:
        # Lấy đường dẫn đầy đủ của email được chọn
            selectedEmailPath = os.path.join(pathRead, readEmailList[selected_index - 1])
        # Đọc nội dung email và hiển thị thông tin
            with open(selectedEmailPath, 'r', encoding='utf-8') as emailFile:
                emailContent = emailFile.read()
                # print(emailContent)
                displayEmail(emailContent)
        ## Nếu email chọn nằm trong folder chưa đọc
        elif readIndex <= selected_index < unReadIndex:
        # Lấy đường dẫn đầy đủ của email được chọn
            selectedEmailPath = os.path.join(pathUnRead, unReadEmailList[selected_index - readIndex])
        # Đọc nội dung email và hiển thị thông tin
            with open(selectedEmailPath, 'r', encoding='utf-8') as emailFile:
                ## In nội dung
                emailContent = emailFile.read()
                displayEmail(emailContent)
                
                ## Cập nhật lại email thành đã được đọc
            moveFile(selectedEmailPath,pathRead)
            readEmailList = listEmailsInFolder(pathRead)
            unReadEmailList = listEmailsInFolder(pathUnRead)
        elif selected_index != 0:
            print("Lựa chọn không hợp lệ.")
            break
#-------------------------------------------------------------------------------------------#
def displayEmail(mailContent):
    headerContentEnd = mailContent.find('--------------')
    textContentEnd = mailContent.find('--------------', headerContentEnd + 1)

    #in nội dung mail
    if  textContentEnd != -1:
        textContent = mailContent[: textContentEnd]
        displayTextContent(textContent)
        #in thông tin tệp đính kèm nếu có 
        attachmentContent = mailContent[textContentEnd:]
        displayAttachment(attachmentContent)
#-------------------------------------------------------------------------------------------# 
def displayTextContent(textContent):

    # thông tin gửi từ đâu
    FromTextStart = textContent.find("From:")
    FromTextEnd = textContent.find("\n", FromTextStart)
    fromText = textContent[FromTextStart : FromTextEnd]


    #in thông tin được gửi theo TO
    ToTextStart = textContent.find("To:")
    ToTextEnd = textContent.find("\n", ToTextStart)
    ToText = textContent[ToTextStart : ToTextEnd]


    #lấy thông tin CC
    CcTextStart = textContent.find("Cc:")
    CcTextEnd = textContent.find("\n", CcTextStart)
    CcText = textContent[CcTextStart : CcTextEnd]
    

    #lấy thông tin Subject
    SubTextStart = textContent.find("Subject:")
    SubTextEnd = textContent.find("\n", SubTextStart)
    subText = textContent[SubTextStart : SubTextEnd]


    #lấy thông tin nội dung mail 
    BodyTextStart = textContent.find("Content-Transfer-Encoding: 7bit") + len("Content-Transfer-Encoding: 7bit") + 2
    BodyTextEnd = textContent.find("--------------", BodyTextStart)
    BodyText = textContent[BodyTextStart : BodyTextEnd].strip("\r\n")

    #in thông tin mail ra console
    print("------------------------------------------------")
    print(fromText)
    print(ToText)
    if(CcText.strip() != "Cc:"):
        print(CcText)
    print("\n",subText)
    print("------------------------------------------------")
    print("\r\n",BodyText)
    print("------------------------------------------------")
#-------------------------------------------------------------------------------------------#
def displayAttachment(textContent):
    attachmentStart = textContent.find('Content-Disposition: attachment')

    attachmentInfoList = []

    while attachmentStart != -1:
        attachmentEnd = textContent.find('--------------', attachmentStart + 1)

        if attachmentEnd == -1:
            break

        # Lấy base64-encoded string
        base64_string = extractBase64EncodedString(textContent, attachmentStart)

        # tách chuỗi để xác định contentType trong tiêu chuẩn 
        contentTypeStart = textContent.find('Content-Type:', attachmentStart, attachmentEnd)
        contentTypeEnd = textContent.find('\r\n', contentTypeStart)
        contentType = textContent[contentTypeStart : contentTypeEnd].strip()

        # tách chuỗi để xác đinh tên của tệp đính kèm 
        attachmentFileNameStart = textContent.find('filename="', attachmentStart) + len('filename="')
        attachmentFileNameEnd = textContent.find('"', attachmentFileNameStart) 
        attachmentFileName = textContent[attachmentFileNameStart : attachmentFileNameEnd].strip()

        # Trích xuất thông tin đính kèm
        attachmentInfoList.append({"filename": attachmentFileName, "base64": base64_string})
        attachmentStart = textContent.find('Content-Disposition: attachment', attachmentEnd + 1)

    # In thông tin các tệp đính kèm
    if attachmentInfoList:
        print("Thư có các tệp đính kèm:")
        count = 1
        for attachmentInfo in attachmentInfoList:
            print(f"{count}. Attachment Filename: {attachmentInfo['filename']}")
            count += 1

        while True:
            try:
                # Lựa chọn thao tác với tệp đính kèm
                selectedIndex = int(input("Nhập số tương ứng với tệp đính kèm bạn muốn thao tác (0 để quay lại MENU): "))

                if 0 < selectedIndex <= len(attachmentInfoList):
                    attachmentSelectedInfo = attachmentInfoList[selectedIndex - 1]
                    attachmentSelectedFilename = attachmentSelectedInfo["filename"]
                    base64_string = attachmentSelectedInfo["base64"].replace("\r\n", "")

                    print("Chọn 0 để quay lại.")
                    print("Chọn 1 để lưu tệp.")

                    selectedIndexWithAt = int(input("Nhập lựa chọn của bạn: "))

                    if selectedIndexWithAt == 0:
                        print("Đã Quay lại.")
                    elif selectedIndexWithAt == 1:
                        savePath = input("Nhập đường dẫn lưu file (ví dụ: /path/to/save/file.txt): ")
                        count = 1
                        #NEW - kiểm tra để lưu file không trùng lặp 
                        while True:
                            # Tạo đường dẫn đầy đủ cho file
                            filePath = os.path.join(savePath, attachmentSelectedFilename)
                            
                            # Kiểm tra xem file có tồn tại không
                            if not os.path.exists(filePath):
                                break
                            
                            # Nếu file đã tồn tại, thêm hậu tố
                            filename, file_extension = os.path.splitext(attachmentSelectedFilename)
                            attachmentSelectedFilename = f"{filename}_{count}{file_extension}"
                            count += 1
                        #lưu file đính kèm 
                        saveAttachment(filePath, base64_string)
                        print("File đã được lưu tại:", savePath)
                        print("Tên tệp trong mã:", attachmentSelectedFilename)
                    else:
                        print("Lựa chọn không hợp lệ.")
                elif selectedIndex == 0:
                    print("Quay lại MENU.")
                    break
                else:
                    print("Lựa chọn không hợp lệ, hãy chọn lại")

            except ValueError:
                print("Lỗi: Bạn phải nhập một số nguyên. Vui lòng thử lại.")

    else:
        print("Không có tệp đính kèm trong thư.")

#-------------------------------------------------------------------------------------------#
def saveAttachment(path, data):

    CHUNK_SIZE = 174
    try:
        with open(path, 'ab') as file:
            for i in range(0, len(data), CHUNK_SIZE):

                chunk = data[i + len("\n"): i + CHUNK_SIZE - 1]

                file.write(base64.b64decode(chunk))

    except Exception as e:
        print(f"Lỗi khi lưu tệp: {e}")
#-------------------------------------------------------------------------------------------#  
def extractBase64EncodedString(textContent, attachmentStart):
    # Tìm vị trí của phần base64-encoded string
    start_index = textContent.find('Content-Transfer-Encoding: base64', attachmentStart) + len('Content-Transfer-Encoding: base64') + 1
    end_index = textContent.find('--------------', start_index)

    # Lấy ra phần base64-encoded string
    base64_string = textContent[start_index:end_index] #NEW FIX 
    return base64_string


#-------------------------------------------------------------------------------------------#    
#kết thúc yêu cầu 3: 
#-------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------#
# Filter
def moveFile(source_path, destination_path):
    try: # update 15/12 tự tạo đường dẫn
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        shutil.move(source_path, destination_path)
        
    except Exception as e:
        print(f"Lỗi không xác định: {e}")

def DisplayListEmail(pathRead,pathUnRead):

    readEmailList = listEmailsInFolder(pathRead)
    unReadEmailList = listEmailsInFolder(pathUnRead)
    readIndex = 1 ##
    for email in readEmailList:
        fromEmail, subject = subjectAndFrom(email,pathRead)
        print(f"{readIndex}. <{fromEmail}>, <{subject}>")
        readIndex = readIndex + 1

    unReadIndex = readIndex
    for email in unReadEmailList:
        fromEmail, subject = subjectAndFrom(email,pathUnRead)
        print(f"{unReadIndex}. (Chưa đọc) <{fromEmail}>, <{subject}>")
        unReadIndex = unReadIndex + 1

    return readIndex, unReadIndex

def subjectAndFrom(fileName,path):
    filePath = os.path.join(path,fileName)
    with open(filePath,'r') as reader:
        textContent = reader.read()
     # thông tin gửi từ đâu
    FromTextStart = textContent.find("From:")
    FromTextEnd = textContent.find("\n", FromTextStart)
    fromText = textContent[FromTextStart : FromTextEnd]

    # Này xử lý chỉ lấy phần tên người gửi 
    FromTextStart = fromText.find(":")
    FromTextEnd = fromText.find("<", FromTextStart)
    fromEmail = fromText[FromTextStart + 1 : FromTextEnd].strip()


    #lấy thông tin Subject
    SubTextStart = textContent.find("Subject:")
    SubTextEnd = textContent.find("\n", SubTextStart)
    subjectText = textContent[SubTextStart : SubTextEnd]

    #lấy nội dung bên trong của Subject
    SubTextStart = subjectText.find(":")
    subject = subjectText[SubTextStart + 1 : len(subjectText)].strip()

    return fromEmail, subject

def filter(path, configFilePath):

    with open(configFilePath, 'r') as file:
        data = json.loads(file.read())

    filterMailList = data['filterMailList']
    filterSubjectList = data['filterSubjectList']
    filterContentList = data['filterContentList']
    filterSpamList = data['filterSpamList']
    # Này sau này bỏ vào config rồi truyền vào


    # Này chỉnh sao cho tương thích với từng chỗ muốn tải về để quản lý
    pathProjectUnread = path.replace("Inbox", "Project")
    pathImportantUnread = path.replace("Inbox", "Important")
    pathWorkUnread = path.replace("Inbox", "Work")
    pathSpamUnread = path.replace("Inbox", "Spam")
    # Này chỉnh sao cho tương thích với từng chỗ muốn tải về để quản lý

    try:
        fileList = os.listdir(path)
    # Thực hiện các hành động với fileList nếu đường dẫn tồn tại
        # print("Danh sách các tệp trong thư mục:", fileList)
    except FileNotFoundError:
    # Xử lý trường hợp đường dẫn không tồn tại
        print(f"Đường dẫn '{path}' không tồn tại.")
    except Exception as e:
    # Xử lý các lỗi khác nếu có
        print(f"Có lỗi xảy ra: {e}")

         
    # mở từng file để đọc
    for fileName in fileList:
        # thêm đường dẫn 
        filePath = os.path.join(path,fileName)
        with open(filePath,'r') as reader:
            textContent = reader.read()

    #  '''khúc này copy tận dụng lại xử lý của hàm display'''
     # thông tin gửi từ đâu
        FromTextStart = textContent.find("From:")
        FromTextEnd = textContent.find("\n", FromTextStart)
        fromText = textContent[FromTextStart : FromTextEnd]
    # Lấy địa chỉ email bên trong < > 
        FromTextStart = fromText.find("<")
        FromTextEnd = fromText.find(">", FromTextStart)
        fromText = fromText[FromTextStart + 1 : FromTextEnd]

    #lấy thông tin Subject
        SubTextStart = textContent.find("Subject:")
        SubTextEnd = textContent.find("\n", SubTextStart)
        subText = textContent[SubTextStart : SubTextEnd]

    #lấy nội dung bên trong của Subject
        SubTextStart = subText.find(":")
        subject = subText[SubTextStart + 1 : len(subText)].strip()

    #lấy thông tin nội dung mail 
        BodyTextStart = textContent.find("Content-Type: text/plain") + len("Content-Type: text/plain")
        BodyTextEnd = textContent.find("--------------", BodyTextStart)
        BodyText = textContent[BodyTextStart : BodyTextEnd].strip("\r\n")


        # while True:
        #     flag = False
        #     for mail in filterMailList :
        #         if mail in fromText:
        #             shutil.move(filePath,pathProjectUnread)
        #             #print("Đã chuyển file đến thư mục Project với đường dẫn là:{}",pathProjectUnread)
        #             flag = True
        #             break
        #     if flag:
        #         break
        #     for sub in filterSubjectList :
        #         if sub in subject:
        #             shutil.move(filePath,pathImportantUnread)
        #             #print("Đã chuyển file đến thư mục Important với đường dẫn là:{}",pathImportantUnread)
        #             flag = True
        #             break
        #     if flag:
        #         break
        #     for content in filterContentList :
        #         if content in BodyText:
        #             shutil.move(filePath,pathWorkUnread)
        #             #print("Đã chuyển file đến thư mục Work với đường dẫn là:{}",pathWorkUnread)
        #             flag = True
        #             break
        #     if flag:
        #         break    
        #     for spam in filterSpamList :
        #         if spam in BodyText or spam in subText:
        #             shutil.move(filePath,pathSpamUnread)
        #             #print("Đã chuyển file đến thư mục Spam với đường dẫn là:{}",pathSpamUnread)
        #             flag = True
        #             break
        #     break
        while True:
            flag = False
            for mail in filterMailList:
                if mail in fromText:
                    if not os.path.exists(pathProjectUnread):
                        os.makedirs(pathProjectUnread)
                    shutil.move(filePath, pathProjectUnread)
                    # print("Đã chuyển file đến thư mục Project với đường dẫn là: {}".format(pathProjectUnread))
                    flag = True
                    break
            if flag:
                break
            for sub in filterSubjectList :
                if sub in subject:
                    if not os.path.exists(pathImportantUnread):
                         os.makedirs(pathImportantUnread)
                    shutil.move(filePath,pathImportantUnread)
                    # print("Đã chuyển file đến thư mục Important với đường dẫn là:{}",pathImportantUnread)
                    flag = True
                    break
            if flag:
                break
            for content in filterContentList :
                if content in BodyText:
                    if not os.path.exists(pathWorkUnread):
                        os.makedirs(pathWorkUnread)
                    shutil.move(filePath,pathWorkUnread)
                    # print("Đã chuyển file đến thư mục Work với đường dẫn là:{}",pathWorkUnread)
                    flag = True
                    break
            if flag:
                break    
            for spam in filterSpamList :
                if spam in BodyText or spam in subText:
                    if not os.path.exists(pathSpamUnread):
                         os.makedirs(pathSpamUnread)
                    shutil.move(filePath,pathSpamUnread)
                    # print("Đã chuyển file đến thư mục Spam với đường dẫn là:{}",pathSpamUnread)
                    flag = True
                    break
            break


#-------------------------------------------------------------------------------------------#
#Menu chọn của bài 
def menu(smtpIp, smtpPort,pop3Server, pop3Port, user, userMail, path, configFilePath):
    isEndProgram = False
    while not isEndProgram:
        print("Vui lòng chọn Menu:")
        print("1. Để gửi email")
        print("2. Để xem danh sách các email đã nhận")
        print("3. để tải mail về mail box của client")
        print("4. Thoát")
        choice = input("Bạn chọn:")

        if choice == '1':
            print("Đây là thông tin soạn email: (nếu không điền vui lòng nhấn enter để bỏ qua)")
            email = inputEmailFromKeyBoard()
            if email != False:
                 sendEmail(smtpIp,smtpPort,user,userMail,email)
            # print("Đây là thông tin soạn email: (nếu không điền vui lòng nhấn enter để bỏ qua)")
            # email = inputEmailFromKeyBoard()
            # sendEmail(smtpIp,smtpPort,user,userMail,email)
        elif choice == '2': 
            displaySelectedEmail(path)
        elif choice == '3':
            getMail(pop3Server, pop3Port, userMail, path, configFilePath)
            filter(path, configFilePath)
        elif choice == '4':
            isEndProgram = True
            print("chương trình đã kết thúc: ")
        else:
            print("\nlựa chọn không hợp lệ vui lòng chọn lại\n".upper())

#-------------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------------------#
# yêu cầu : AUTO LOAD MAIL
def autoGetMail(POP3Server, POP3Port, userName, outputFolder, configFilePath):
    #tạo socket kết nối đến máy chủ pop3 
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    clientSocket.connect((POP3Server, POP3Port))
    #nhận và hiện thị phản hồi từ máy chủ 
    response = clientSocket.recv(1024)

    #gửi lệnh USER để xác định tên người dùng 
    userCommand = "USER {}\r\n".format(userName)
    clientSocket.sendall(userCommand.encode())
    response = clientSocket.recv(1024)

    #gửi lệnh LIST để lấy danh sách thư mục 
    listCommand = "LIST\r\n"
    clientSocket.sendall(listCommand.encode())
    response = clientSocket.recv(1024)

    # gửi lệnh UIDL để kiểm tra các mail chưa được tải về 
    uidlCommand = "UIDL\r\n"
    clientSocket.sendall(uidlCommand.encode())
    response = clientSocket.recv(1024)

    #xử lí chuỗi sau khi gửi mã UIDL để nhận được danh sách các mail chưa được tải về 
    uidList = response.decode().split('\r\n')[1:-2]

    count = 0;
    for mailNumber in uidList:
        if not isCodeInFile(str(mailNumber.split()[1]), configFilePath):
            addCodeToFile(str(mailNumber.split()[1]), configFilePath)
            saveMail(clientSocket, int(mailNumber.split()[0]), mailNumber.split()[1], outputFolder)
            count += 1
    


    # Gửi lệnh QUIT và đóng kết nối
    quitCommand = "QUIT\r\n"
    clientSocket.sendall(quitCommand.encode())
    response = clientSocket.recv(1024)
    
    #giải phóng socket 
    clientSocket.close()
    return count

# ta cần viết lại hàm getMail để khi chia luồng xử lí ta sẽ không in thông tin ra console nữa 
# ta tạo thêm một toàn cục(global) để kiểm soát quá trình autoLoadMail
# should_stop_auto_load = False
loadMailWhenStartProgram = False

def autoLoadMail(pop3Server, pop3Port, userMail, path, intervalMinutes, configFilePath):
    # global should_stop_auto_load
    global loadMailWhenStartProgram

    while True:
        count = autoGetMail(pop3Server, pop3Port, userMail, path, configFilePath)
        filter(path, configFilePath)
        
        #NEW - thêm điều kiện tải mail khi khởi chạy chương trình 
        if not loadMailWhenStartProgram:
            loadMailWhenStartProgram = True
            if count != 0:
                print("bạn có {} mail mới".format(count))
            else: 
                print("bạn không có mail mới")

        # Load after time
        time.sleep(intervalMinutes)

def readConfigFile(configFilePath):
    #mở file để đọc nội dung
    # current_directory = os.path.dirname(os.path.abspath(__file__))
    # # nối thành đường dẫn cần đến để đọc file
    # dpath = os.path.join(current_directory, 'config.json')
    with open(configFilePath, 'r') as file:
        data = json.loads(file.read())

    #trích xuất các thông tin trong file json
    userName = data['userName']
    userMail = data['userMail']
    serverName = data['serverName']
    smtpPort = data['smtpPort']
    pop3Port = data['pop3Port']
    path = data['path']
    intervalMinutes = data['intervalMinutes']
    
    return userName, userMail, serverName, smtpPort, pop3Port, path, intervalMinutes

#-------------------------------------------------------------------------------------------#
def main():

    global loadMailWhenStartProgram
    configFilePath = "D:\Socket\socket-py\Mail-Client\config.json"
    
    # đọc thông tin từ file json 
    userName, userMail, serverName, smtpPort, pop3Port, path, intervalMinutes = readConfigFile(configFilePath)

    #kiểm tra đường dẫn có hợp lệ hay không nếu không thì tạo đường dẫn 
    #NEW
    if not os.path.exists(path):
        os.makedirs(path)
    
    #tạo 1 luồng để chạ autoLoadMail dưới nền 
    autoLoadMailThread = threading.Thread(target = autoLoadMail, args=(serverName, pop3Port, userMail, path, intervalMinutes, configFilePath), daemon=True)
    autoLoadMailThread.start()
    # Menu
    time.sleep(4) #thời gian chờ lần load mail đầu tiên    
    menu(serverName, smtpPort, serverName, pop3Port, userName,userMail,path, configFilePath)

    # sau khi menu kết thúc ta kích hoạt biến dừng để thoát

#-------------------------------------------------------------------------------------------#
#sử dụng file json để lưu lại các thông tin của file đã tải xuống từ mail box
def loadDataFromFile(fileName):
    try:
        with open(fileName, "r") as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        # Nếu file không tồn tại, trả về một đối tượng JSON rỗng
        data = {"specialCodes": []}
    return data

def save_data_to_file(data, fileName):
    with open(fileName, "w") as json_file:
        json.dump(data, json_file, indent=2)

def addCodeToFile(newCode, fileName):
    data = loadDataFromFile(fileName)
    
    # Thêm mã mới vào danh sách mã đặc biệt nếu nó chưa tồn tại
    if newCode not in data["specialCodes"]:
        data["specialCodes"].append(newCode)
        save_data_to_file(data, fileName)

def removeCodeFromFile(codeToRemove, fileName):
    data = loadDataFromFile(fileName)

    # Xóa mã khỏi danh sách mã đặc biệt nếu nó tồn tại
    if codeToRemove in data["specialCodes"]:
        data["specialCodes"].remove(codeToRemove)
        save_data_to_file(data, fileName)

def isCodeInFile(codeToCheck, fileName):
    data = loadDataFromFile(fileName)
    return codeToCheck in data["specialCodes"]

#-------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    main()