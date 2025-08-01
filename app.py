from flask import Flask,request,render_template,url_for,redirect,flash,session,send_file
from flask_session import Session
from io import BytesIO
from otp import generate_otp
from stoken import entoken,dntoken
from Cmail import send_mail
import flask_excel as excel
from mimetypes import guess_type

import mysql.connector
mydb=mysql.connector.connect(user='root',password='Kalpana147/dpc',host='localhost',db='snmprj')

app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app)
excel.init_excel(app)
app.secret_key='parthiv@29'



@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        gender=request.form['gender']
        cursor=mydb.cursor()
        cursor.execute('select count(*) from users where useremail=%s',[email])
        count_email = cursor.fetchone()
        cursor.close()
        if count_email[0]==0:   
            gotp=generate_otp()
            userdata={'username':username,'useremail':email,'userpassword':password,'usergender':gender,'stored_otp':gotp}
            subject = 'OTP Verification'
            body = f'Your OTP is {gotp}'
            send_mail(to=email, subject=subject, body=body)
            flash(f'OTP has been sent to given email {email}')
            return redirect(url_for('otpverify',udata=entoken(userdata)))
        elif count_email[0]==1:
            flash(f'{email} already exists, use different email')
    return render_template('register.html')

@app.route('/otpverify/<udata>',methods=['GET','POST'])
def otpverify(udata):
    if request.method=='POST':
        user_otp=request.form['OTP']
        try:
            decrypted_otp=dntoken(udata)
        except Exception as e:
            print(f'Error is {e}')
            flash('Can not store your details pls reload the page')
            return redirect(url_for('register'))
        else:
            if decrypted_otp['stored_otp']==user_otp:
                cursor=mydb.cursor()
                cursor.execute('insert into users(username,useremail,password,gender) values(%s,%s,%s,%s)',[decrypted_otp['username'],decrypted_otp['useremail'],decrypted_otp['userpassword'],decrypted_otp['usergender']])
                mydb.commit()
                cursor.close()
                flash('Details registerd successfully')
                return redirect(url_for('login'))
            else:
                flash('OTP was wrong')
                return redirect(url_for('register'))
    return render_template('otp.html')

@app.route('/login',methods=['GET','POST'])
def login():
    
    if request.method=='POST':
        uemail=request.form['useremail']
        password=request.form['userpassword']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        count_useremail=cursor.fetchone()
        print(count_useremail)
        if count_useremail[0]==1:
            cursor.execute('select password from users where useremail=%s',[uemail])
            stored_password=cursor.fetchone()
            if stored_password[0]==password:
                session['user']=uemail
                return redirect(url_for('dashboard'))
            else:
                flash('password is wronf try again')
                return redirect(url_for('login'))
        elif count_useremail[0]==0:
            flash('Email not found pls register first')
            return redirect(url_for('login'))       
    return render_template('login.html')
    

@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        useremail=request.form['useremail']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[useremail])
        count_useremail=cursor.fetchone()
        if count_useremail[0]==1:
            subject = 'Reset link for password update'
            body=f"click on the given link : {url_for('newpassword',data=entoken(useremail),_external=True)}"
            send_mail(to=useremail,subject=subject,body=body)
            flash(f'Reset link has been sent to given email {useremail}')
            return redirect(url_for('forgotpassword'))
        elif count_useremail[0]==0:
            flash("email not found pls register")
            return redirect(url_for('login'))

    return render_template('forget.html')

@app.route('/newpassword/<data>', methods=['GET', 'POST'])
def newpassword(data):
    if request.method == 'POST':
        npassword = request.form['newpassword']
        cpassword = request.form['confirmpassword']
        try:
            decrypt_email = dntoken(data)
        except Exception as e:
            print(e)
            flash('Could not fetch new password update link')
            return redirect(url_for('forgotpassword'))
        else:
            if npassword == cpassword:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where useremail=%s', [npassword, decrypt_email])
                mydb.commit()
                cursor.close()
                flash('Password updated successfully')
                return redirect(url_for('login'))
            else:
                flash('Passwords do not match')
                return redirect(url_for('newpassword', data=data))
    return render_template('newpassword.html')


@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('You need to login first')
        return redirect(url_for('login'))

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,description,added_by) values(%s,%s,%s)',[title,description,session.get('user')])
            mydb.commit()
            cursor.close()
            flash(f'{title} added succesfully')
            return redirect(url_for('dashboard'))
        return render_template('addnotes.html')
    else:
        flash('pls login first')
        return redirect(url_for('login'))
    
@app.route('/viewnotes')
def viewnotes():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM notes WHERE added_by = %s', [session.get('user')])
        notes_data = cursor.fetchall()
        print(notes_data)
        return render_template('viewnotes.html', notes_data=notes_data)
    else:
        flash('pls login first')
        return redirect(url_for('login'))
    
@app.route('/viewnote/<nid>')
def viewnote(nid):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM notes WHERE nid = %s AND added_by = %s', [nid, session.get('user')])
    note_data = cursor.fetchone()
    if note_data:
        return render_template('viewnote.html', note_data=note_data)
    else:
        flash('Note not found or you do not have permission to view it.')
        return redirect(url_for('viewnotes'))


@app.route('/delete/')
def delete():
    if session.get('user'):
        nid = request.args.get('nid')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('DELETE FROM notes WHERE nid = %s AND added_by = %s', [nid, session.get('user')])
        mydb.commit()
        cursor.close()
        flash('Note deleted successfully')
        return redirect(url_for('viewnotes'))
    else:
        flash('You need to login first')
        return redirect(url_for('login'))


@app.route('/update/<nid>', methods=['GET', 'POST'])
def update(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM notes WHERE nid = %s AND added_by = %s', [nid, session.get('user')])
        note_data = cursor.fetchone()
        print(note_data)
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            cursor.execute('UPDATE notes SET title = %s, description = %s WHERE nid = %s AND added_by = %s', 
                           [title, description, nid, session.get('user')])
            mydb.commit()
            cursor.close()
            flash('Note updated successfully')
            return redirect(url_for('viewnotes'))
        return render_template('update.html', note_data=note_data)
    else:
        flash('You need to login first')
        return redirect(url_for('login'))

@app.route('/fileupload', methods=['GET', 'POST'])
def fileupload():
    if session.get('user'):
        if request.method == 'POST':
            filedata = request.files['file']
            fname = filedata.filename
            fdata = filedata.read()
            cursor = mydb.cursor(buffered=True)
            cursor.execute(
    'INSERT INTO filedata (file_name, file_data, added_by) VALUES (%s, %s, %s)',
    [fname, fdata, session.get('user')]
)

            mydb.commit()
            cursor.close()
            flash(f'File {fname} uploaded successfully')
            return redirect(url_for('fileupload'))

        return render_template('fileupload.html')
    else:
        flash('You need to login first')
        return redirect(url_for('login'))

@app.route('/viewfiles')
def viewfiles():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from filedata where added_by=%s',[session.get('user')])
    files_data=cursor.fetchall()
    print(files_data)
    return render_template('viewfiles.html',files_data=files_data)
@app.route('/view_file/<fid>')
def view_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fid,file_name,file_data from filedata where fid=%s and added_by=%s',[fid,session.get('user')])
        fdata=cursor.fetchone()
        data=BytesIO(fdata[2])
        mime_type, _ = guess_type(fdata[1])
        return send_file(data,download_name=fdata[1],mimetype=mime_type or 'application/ocatat-stream',as_attachment=False)
    else:
        flash('please login first') 
        return redirect(url_for('login')) 

@app.route('/download_file/<fid>')
def download_file(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT fid, file_name, file_data FROM filedata WHERE fid = %s AND added_by = %s', [fid, session.get('user')])
        fdata = cursor.fetchone()
        data = BytesIO(fdata[2])
        mime_type, _ = guess_type(fdata[1])
        return send_file(data, download_name=fdata[1], mimetype=mime_type or 'application/octet-stream', as_attachment=True)
    else:
        flash('please login first')
        return redirect(url_for('login'))

@app.route('/delete_file/', methods=['POST'])
def delete_file():
    if session.get('user'):
        fid = request.args.get('fid')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('DELETE FROM filedata WHERE fid = %s AND added_by = %s', [fid, session.get('user')])
        mydb.commit()
        cursor.close()
        flash('File deleted successfully')
        return redirect(url_for('viewfiles'))
    else:
        flash('You need to login first')
        return redirect(url_for('login'))


# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     if session.get('user'):
#         if request.method == 'POST':
#             search_query = request.form['search_query']
#             pattern = re.compile(r'^[a-zA-Z0-9\s]+$')
#             print(pattern)
#             if re.match(pattern):
                
            
#         return render_template('search.html')
#     else:
#         flash('You need to login first')
#         return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if session.get('user'):
        if request.method == 'POST':
            search_query = request.form['search_query']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('SELECT * FROM notes WHERE added_by = %s AND (title LIKE %s OR description LIKE %s)', 
                           [session.get('user'), f'%{search_query}%', f'%{search_query}%'])
            search_results = cursor.fetchall()
            cursor.close()
            return render_template('search_results.html', search_results=search_results, search_query=search_query)
        return render_template('search.html')
    else:
        flash('You need to login first')
        return redirect(url_for('login'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where added_by = %s',[session.get('user')])
        stored_data=cursor.fetchall()
        if stored_data:
            array_data=[list(i) for i in stored_data]
            columns=['NOTES_ID','TITLE','DESCRIPTION','CREATED_AT']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
        else:
            flash('no data found')
            return redirect(url_for('dashboard')) 
    else:
        flash('please login first')
        return redirect(url_for('login'))    



@app.route('/userlogout', methods=['GET', 'POST'])
def userlogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('You need to login first')
        return redirect(url_for('login'))

        

app.run(debug=True,use_reloader=True)