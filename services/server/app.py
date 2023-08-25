from flask import Flask,jsonify,request,render_template
from redis import Redis

app = Flask(__name__)
redis = Redis(host='redis', port=6379)

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        response_body = {
            "name": "Hello World",
            "about" :"testing, 123",
            "foo": "bar"
        }
#   return 'DEFINED ROUTE DIR', 200
    return response_body

@app.route('/test')
def hello():
    redis.incr('hits')
    counter = str(redis.get('hits'),'utf-8')
    return "Welcome to this webpage!, This webpage has been viewed "+counter+" time(s)"

@app.route('/name_receiver', methods=['GET'])
def name_receiver():
    if request.method == 'GET':

        # redis add request.args.get('name') to a list in db
        redis.lpush('name_list', request.args.get('name'))

        # redis get the list
        name_list = redis.lrange('name_list', 0, -1)
        name_value_string = "<br>".join(str(name, 'utf-8') for name in name_list)
        # return the list as a string of values with line breaks
        return render_template('index.html', name_vals=name_value_string)
        #return "<h1> Name List</h1>"+"<br>".join(str(name, 'utf-8') for name in name_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')