from django.core.mail import send_mail
email_title = '邮件标题'
email_body = '邮件内容'
email = '1751394821@qq.com'  #对方的邮箱
send_status = send_mail(email_title, email_body,"", [email])

if send_status:
    print("===========")
else:
    print("----------------")
