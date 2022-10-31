from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired


class DrawingForm(FlaskForm):
    shape_options = [("1", "1"), ("2", "2"), ("3", "3")]
    color_options = [("RED", "Red"), ("GREEN", "Green"), ("BLUE", "Blue")]
    frame = RadioField("Frame shape: ", choices=shape_options, validators=[DataRequired()])
    screen = RadioField("Screen shape: ", choices=shape_options, validators=[DataRequired()])
    keyboard = RadioField("Keyboard shape: ", choices=shape_options, validators=[DataRequired()])
    f_color = RadioField("Frame color: ", choices=color_options, validators=[DataRequired()])
    s_color = RadioField("Screen color: ", choices=color_options, validators=[DataRequired()])
    k_color = RadioField("Keyboard color: ", choices=color_options, validators=[DataRequired()])
    submit = SubmitField("Add Order")
