from django.shortcuts import render,redirect
from .models import User,ConfirmString
from .form import UserForm,RegisterForm
from mysite import settings

import hashlib
import datetime

#利用哈希对密码进行加密
def hash_code(s, salt='mysite'):# 加点盐
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()
# Create your views here.
def index(request):
    return render(request,'login/index.html')

def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    ConfirmString.objects.create(code=code, user=user,)
    return code

def send_email(email, code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自的登录注册网站的注册确认邮件'

    text_content = '''感谢注册
                    如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''

    html_content = '''
                    <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>注册登录界面网站</a>！</p>
                    <p>请点击站点链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format('127.0.0.1:8000', code,settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def login(request):
    #如果已经登录过了，则返回首页
    if request.session.get('is_login', None):
        return redirect("/")
    if request.method=="POST":
        login_form = UserForm(request.POST)#在提交表单后接受表单
        message = "请检查填写的内容"
        if login_form.is_valid():#验证表单，如果验证不成功就会将表单原始数据打包返回给前端页面，而不是返回一个空表单。
            username = login_form.cleaned_data["username"]#验证成功后从表单对象的该字典中提取表单数据
            password = login_form.cleaned_data["password"]
            try:#验证用户是否注册过
                user = User.objects.get(name=username)
                if not user.has_confirmed:#验证用户是否邮箱验证过
                    message = "该用户还未通过邮件确认！"
                    return render(request, 'login/login.html', locals())
                if hash_code(password) == user.password:
                    #登录成功，会话保持
                    request.session["is_login"] = True#记录是否登录
                    request.session["user_id"] = user
                    request.session["user_name"] = user.name
                    return redirect("/")
                else:
                    message = "密码错误！"
            except:
                message = "用户不存在"
        return render(request,'login/login.html',locals())
    login_form = UserForm()#实例化表单
    return render(request, 'login/login.html',locals())

def register(request):
    if request.session.get('is_login', None):
        # 登录状态不允许注册。你可以修改这条原则！
        return redirect("/")
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():  # 获取数据
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不同！"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = User.objects.filter(name=username)
                if same_name_user:  # 用户名唯一
                    message = '用户已经存在，请重新选择用户名！'
                    return render(request, 'login/register.html', locals())
                same_email_user = User.objects.filter(email=email)
                if same_email_user:  # 邮箱地址唯一
                    message = '该邮箱地址已被注册，请使用别的邮箱！'
                    return render(request, 'login/register.html', locals())

                # 当一切都OK的情况下，创建新用户

                new_user = User()
                new_user.name = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                #发送邮件
                code = make_confirm_string(new_user)
                send_email(email, code)
                message = '请前往注册邮箱，进行邮件确认！'
                return render(request, 'login/confirm.html', locals())  # 跳转到等待邮件确认页面
    register_form = RegisterForm()
    return render(request, 'login/register.html', locals())

def logout(request):
    if request.session.get("is_login",None):
        request.session.flush()#删除session，退出登录
    return redirect("/")

#用户新浪邮箱验证
def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求!'
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time + datetime.timedelta(settings.CONFIRM_DAYS)
    print("================ctime",c_time)
    now_time = datetime.datetime.now()+datetime.timedelta(0)
    print("------------------ntime",now_time)
    if now_time > c_time:
        confirm.user.delete()
        message = '您的邮件已经过期！请重新注册!'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登录！'
        return render(request, 'login/confirm.html', locals())