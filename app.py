from flask import Flask, flash, render_template, request, redirect, url_for, make_response, session
from flask_jwt_extended import JWTManager, set_access_cookies, jwt_required, unset_jwt_cookies
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
secretKey = os.getenv("SECRET_KEY")

# set app secret key
app.secret_key = secretKey

# set jwt secret key
app.config['JWT_SECRET_KEY'] = secretKey

# set lokasi penyimpanan jwt yang diget pas login
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

# nonaktifin jwt csrf protect
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

# inisialisasi JWTManager supaya fungsi2 untuk ngatur jwt bisa dipake
jwt = JWTManager(app)

# set base url API
BASE_URL = "http://127.0.0.1:8000"

def get_employees():
    if not 'jwt_token' in session:
        return "no session found"
    
    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"

    # kirim get request ke API untuk dapetin data user (di bagian header authorization diisi jwt token)
    data = requests.get(f"{BASE_URL}/api/users", headers={"Authorization": jwtToken})
    data = data.json()
    
    if data["operation_status"] == -15:
        return "token expired"

    if data["message"] != 'OK':
        return "no data"

    userData = []

    # iterasi melalui setiap entitas user di dalam data
    for nodeId, userInfo in data['data'].items():
        userId = userInfo.get('user_id', '')
        name = userInfo.get('name', '')
        floor = userInfo.get('floor', '')
        email = userInfo.get('email', '')


        if name == "admin":
            continue
        # nambahin data user ke dalam list user_data
        userData.append({'id': userId, 'name': name, 'floor': floor, 'email': email})
    
    return userData

@app.route("/")
def index():
    return redirect(url_for("dashboard"))

# method untuk mengembalikan ke halaman login bagi user yang tidak login dan mencoba mengakses halaman yang terproteksi 
@jwt.unauthorized_loader
def unauthorized_access(_err):
    return redirect(url_for("login"))

@app.route('/login', methods=["GET", "POST"])
def login():

    # cek method http request yang masuk ke endpoint
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # cek lagi kalo email udah diisi
        if email and password:

            # set data login
            loginData = {
                "email": email,
                "password": password,
            }

            # kirim post request ke API untuk login
            login = requests.post(f"{BASE_URL}/api/login", data=loginData)

            # dapetin data login dalam bentuk json
            userLoginData = login.json()

            # cek kalo email or password salah
            if userLoginData['operation_status'] == -8:
                return render_template("auth/login.html",)

            # dapetin role user
            userRole = userLoginData['data']['user']['role']

            # cek kalo login gagal by status code dan role nya bukan admin
            if login.status_code != 200 or userRole != 1:
                return render_template("auth/login.html",)
            
            # dapetin token JWT lewat response login
            accessToken = userLoginData['token']

            # bikin responsenya langsung redirect ke dashboard
            response = make_response(redirect(url_for('dashboard')))

            # set cookies response pake token JWT yang didapet sebelumnya
            set_access_cookies(response, accessToken)

            # simpan token jwt ke dalam session
            session['jwt_token'] = accessToken

            return response
        
    return render_template("auth/login.html",)

@app.route('/logout', methods=["GET"])
def logout():
    response = make_response(redirect(url_for('login')))
    unset_jwt_cookies(response)
    return response

@app.route('/dashboard', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def dashboard():
     # ambil jwt token dari session
    if not 'jwt_token' in session:
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")
    
    jwtToken = f"Bearer {session['jwt_token']}"
    
    data = requests.get(f"{BASE_URL}/api/users/attendance-logs", headers={"Authorization": jwtToken})
    data = data.json()

    if data['operation_status'] == -15:
        flash("Your session has expired, please login again", "error")
        return render_template("auth/login.html")

    employeesData = get_employees()

    attendanceData = []

    if data["message"] != 'OK':
        attendanceData = []
        return render_template("index.html", attendanceData=attendanceData, employeesData=employeesData)
    

    # iterasi melalui setiap entitas user di dalam data
    for nodeId, timestampInfo in data['data'].items():
        for timestampInfo, userInfo in timestampInfo.items():
            floor = userInfo.get('floor', '')
            status = userInfo.get('status', '')
            timestamp = userInfo.get('timestamp', '')
            
            convertedTimestamp = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M")
            currentDay = datetime.now(ZoneInfo('Asia/Jakarta'))
            
            # ambil data kehadiran hari ini
            if convertedTimestamp.date() == currentDay.date():
                # Tambahkan data user ke dalam list attendanceData
                attendanceData.append({
                    'floor': floor, 
                    'status': status, 
                    'timestamp': timestamp, 
                    })
    
    if employeesData == 'no data':
        employeesData = {}
        return render_template("index.html", attendanceData=attendanceData, employeesData=employeesData)
    
    return render_template("index.html", attendanceData=attendanceData, employeesData=employeesData)

@app.route('/employees', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def employees():

    userData = get_employees()

    if userData == 'no session found':
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")
    
    elif userData == 'token expired':
        flash("Your session has expired, please login again", "error")
        return render_template("auth/login.html")
    
    elif userData == 'no data':
        userData = {}
        return render_template("employees.html", data=userData)
    
    return render_template("employees.html", data=userData)

@app.route('/gallery', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def gallery():
    return render_template("",)

@app.route('/register', methods=["POST"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def register():

    if not 'jwt_token' in session:
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")

    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"

    # cek method http request yang masuk ke endpoint
    if request.method == "POST":
        nip = request.form.get("nip")
        name = request.form.get("name")
        floor = request.form.get("floor")
        email = request.form.get("email")
        password = request.form.get("password")
        profile_picture = request.files.get("profilePicture")

        # cek lagi kalo email udah diisi
        if nip and name and floor and email and password:

            # set data login
            userData = {
                "id_number": nip,
                "name": name,
                "floor": floor,
                "email": email,
                "password": password,
            }

            files = {
                'image_file': (profile_picture.filename, profile_picture.stream, profile_picture.mimetype)
            }

            # kirim post request ke API untuk login
            response = requests.post(f"{BASE_URL}/api/users", files=files, data=userData, headers={"Authorization": jwtToken})
            response = response.json()
            print(response)

            if response['operation_status'] == -15:
                flash("Your session has expired, please login again", "error")
                return render_template("auth/login.html")

            # tambahin validasi jika request post berhasil, maka ada pesannya
            if response["operation_status"] != 1:
                flash(response["message"], 'error')
                return redirect(url_for("employees"))

            flash(response["message"], "success")
            return redirect(url_for("employees"))
        
        flash("Please fill all the forms!", 'error')

    return redirect(url_for("employees"))

@app.route('/update-user/<int:user_id>', methods=["POST"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def update_user(user_id):

    if not 'jwt_token' in session:
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")
    
    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"

    # cek method http request yang masuk ke endpoint
    if request.method == "POST":
        name = request.form.get("name")
        floor = request.form.get("floor")
        email = request.form.get("email")
        profile_picture = request.files.get("profilePicture")

        # set data login
        userData = {
            "name": name,
            "floor": floor,
            "email": email,
        }

        files = {
            'image_file': (profile_picture.filename, profile_picture.stream, profile_picture.mimetype)
        }

        # kirim post request ke API untuk login
        response = requests.put(f"{BASE_URL}/api/users/{user_id}", files=files, data=userData, headers={"Authorization": jwtToken})
        response = response.json()

        # tambahin validasi jika request post berhasil, maka ada pesannya
        if 'message' not in response:
            flash(response['detail'][0]['msg'], 'error')
            return redirect(url_for("employees"))

        if response['operation_status'] == -15:
                flash("Your session has expired, please login again", "error")
                return render_template("auth/login.html")

        if response["operation_status"] != 1:
            flash(response["message"], 'error')
        
        flash(response["message"], "success")
        return redirect(url_for("employees"))
    
    return redirect(url_for("employees"))

@app.route('/delete-user/<int:user_id>', methods=["POST"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def delete_user(user_id):

    if not 'jwt_token' in session:
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")
    
    jwtToken = f"Bearer {session['jwt_token']}"

    if request.method == "POST":
        if request.form.get('_method') == 'DELETE':
            data = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers={"Authorization": jwtToken})
            
            if not data:
                flash("Failed to delete user data", "error")

            data = data.json()

            if data['operation_status'] == -15:
                flash("Your session has expired, please login again", "error")
                return render_template("auth/login.html")
            
            flash(data["message"], "succcess")
            return redirect(url_for("employees"))
    
    return redirect(url_for("employees"))


@app.route('/attendances-log', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def attendances_log():

    if not 'jwt_token' in session:
        flash("No session found, please login again", "error")
        return render_template("auth/login.html")
    
    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"
    
    data = requests.get(f"{BASE_URL}/api/users/attendance-logs", headers={"Authorization": jwtToken})
    data = data.json()

    if data['operation_status'] == -15:
        flash("Your session has expired, please login again", "error")
        return render_template("auth/login.html")
    
    if data["message"] != 'OK':
        return render_template("attendance.html")
        
    userData = []

    # iterasi melalui setiap entitas user di dalam data
    for nodeId, timestampInfo in data['data'].items():
        for timestampInfoKey, userInfo in timestampInfo.items():
            userId = userInfo.get('user_id', '')
            name = userInfo.get('name', '')
            floor = userInfo.get('floor', '')
            status = userInfo.get('status', '')
            timestamp = userInfo.get('timestamp', '')
            captured_image = userInfo.get("captured_face_url", "")

            
            # Tambahkan data user ke dalam list userData
            userData.append({
                'id': userId, 
                'name': name, 
                'floor': floor, 
                'status': status, 
                'timestamp': timestamp, 
                'captured_image': captured_image
                })
    
    
    return render_template("attendance.html", data=userData)

if __name__ == "__main__":
    app.run(debug=True)
