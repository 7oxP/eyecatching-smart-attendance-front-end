from flask import Flask, render_template, request, redirect, url_for, make_response, session
from flask_jwt_extended import JWTManager, set_access_cookies, jwt_required, unset_jwt_cookies
import requests

app = Flask(__name__)

# set app secret key
app.secret_key = "ini_secret"

# set jwt secret key
app.config['JWT_SECRET_KEY'] = '3f2d7dd6853766b9a065bde16186be1a943fd2159594037522c62109e6868f3b'

# set lokasi penyimpanan jwt yang diget pas login
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

# nonaktifin jwt csrf protect
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

# inisialisasi JWTManager supaya fungsi2 untuk ngatur jwt bisa dipake
jwt = JWTManager(app)

# set base url API
BASE_URL = "https://eyecatching-image-ghhipha43a-uc.a.run.app"

@app.route("/")
def index():
    return "Hello"

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
    return render_template("index.html",)

@app.route('/employees', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def employees():

    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"

    # kirim get request ke API untuk dapetin data user (di bagian header authorization diisi jwt token)
    data = requests.get(f"{BASE_URL}/api/users", headers={"Authorization": jwtToken})
    data = data.json()

    userData = []

    # iterasi melalui setiap entitas user di dalam data
    for nodeId, userInfo in data['data'].items():
        userId = userInfo.get('user_id', '')
        name = userInfo.get('name', '')
        floor = userInfo.get('floor', '')

        # nambahin data user ke dalam list user_data
        userData.append({'id': userId, 'name': name, 'floor': floor})
    
    return render_template("employees.html", data=userData)

@app.route('/gallery', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def gallery():
    return render_template("",)

@app.route('/register', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def register():
    return render_template("auth/register.html",)

@app.route('/attendances-log', methods=["GET"])
# method untuk ngasih tau flask bahwa endpoint ini butuh jwt token kalo mau ngakses
@jwt_required()
def attendances_log():
    # ambil jwt token dari session
    jwtToken = f"Bearer {session['jwt_token']}"
    
    data = requests.get(f"{BASE_URL}/api/users/attendance-logs", headers={"Authorization": jwtToken})
    data = data.json()
    
    userData = []

    # iterasi melalui setiap entitas user di dalam data
    for nodeId, timestampInfo in data['data'].items():
            for timestampInfo, userInfo in timestampInfo.items():
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
