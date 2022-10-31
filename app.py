import math
from flask import Flask, render_template, redirect, url_for, request
from orchestrator import Workstation
from forms import DrawingForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'FAST-Lab'

ws_id = '9'
dest_url = '192.168.0.61:5000/events'
ip_conveyor = '192.168.' + ws_id + '.2'
ip_robot = '192.168.' + ws_id + '.1'

my_workstation = Workstation(ws_id, ip_conveyor, ip_robot, dest_url)


@app.route('/', methods=["GET", "POST"])
def index():  # put application's code here
    my_workstation.update_all()
    drawing_form = DrawingForm(csrf_enabled=False)

    if drawing_form.validate_on_submit():
        frame = drawing_form.frame.data
        screen = drawing_form.screen.data
        keyboard = drawing_form.keyboard.data
        f_color = drawing_form.f_color.data
        s_color = drawing_form.s_color.data
        k_color = drawing_form.k_color.data
        print(frame, screen, keyboard)
        return redirect(url_for('new_order',
                                frame=frame, f_color=f_color,
                                screen=screen, s_color=s_color,
                                keyboard=keyboard,  k_color=k_color,
                                _scheme='HTTP', _external=True))

    return render_template("orchestrator.html",
                           form=drawing_form,
                           zones=my_workstation.zones,
                           ws_id=ws_id,
                           ip_conveyor=ip_conveyor,
                           ip_robot=ip_robot,
                           completed_orders=my_workstation.completed_orders,
                           history=my_workstation.history,
                           subscription=my_workstation.subscribed_events,
                           color=my_workstation.pen_color,
                           processing_orders=my_workstation.list_order,
                           pending_orders=my_workstation.pending_orders)


@app.route('/transfer/<int:two_digits>')
def transfer(two_digits):
    latter = str(two_digits % 10)
    former = str(math.floor(two_digits / 10))
    print("Transferring " + former + " " + latter)
    my_workstation.trans_zone(former, latter)
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/change_pen/<string:new_color>')
def change_pen(new_color):
    if new_color == my_workstation.pen_color:
        print("The pen is already attached!")

    else:
        print("Changing pen " + new_color)
        my_workstation.change_pen(new_color)

    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/draw/<int:recipe>')
def draw(recipe):
    recipe = str(recipe)
    print("Drawing recipe " + recipe)
    my_workstation.draw_recipe(recipe)
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/calibrate')
def calibrate():
    my_workstation.calibrate()
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/replace_paper')
def replace_paper():
    my_workstation.replace_paper()
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/subscribe_event/<string:target>/<string:event_id>')
def subscribe(target, event_id):
    my_workstation.subscribe_event(target, event_id)
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/unsubscribe_event/<string:target>/<string:event_id>')
def unsubscribe(target, event_id):
    my_workstation.unsubscribe_event(target, event_id)
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/subscribe_all')
def subscribe_all():
    my_workstation.subscribe_all()
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/unsubscribe_all')
def unsubscribe_all():
    my_workstation.unsubscribe_all()
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/events', methods=['POST'])
def event():
    json = request.json
    my_workstation.event_handler(json)
    return json


@app.route('/new_order/<frame>/<f_color>/<screen>/<s_color>/<keyboard>/<k_color>')
def new_order(frame, f_color, screen, s_color, keyboard, k_color):
    my_workstation.new_order(frame, screen, keyboard, f_color, s_color, k_color)
    return redirect(url_for('index', _scheme='HTTP', _external=True))


@app.route('/new_order/random')
def random_order():
    my_workstation.random_order()
    return redirect(url_for('index', _scheme='HTTP', _external=True))


if __name__ == '__main__':
    app.run()
