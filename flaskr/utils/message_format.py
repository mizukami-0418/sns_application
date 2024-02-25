from flask import url_for
from jinja2.utils import urlize
from flask_login import current_user
from flaskr.utils.template_filters import replace_newline

def make_message_format(user, messages):
  message_tag = ''
  for message in messages:
    message_tag += '<div class="col-lg-1 col-md-1 col-sm-2 col-2">'
    if user.picture_path:
      message_tag += f'<img class="user-image-mini" src={ url_for("static", filename=user.picture_path) }'
    message_tag += f'''
      <p>{ user.username }</p>
      </div>
      <div class="speech-bubble-dest col-lg-4 col-md-7 col-sm-6 col-6">
    '''
    for splitted_message in replace_newline(message.message):
      message_tag += f'<p>{ urlize(splitted_message) }<p>'
    message_tag += '''
      </div>
      <div class="col-lg-7 col-md-3 col-sm-4 col-4"></div>
    '''
  return message_tag

def make_old_message_format(user, messages):
  message_tag = ''
  for message in messages[::-1]:
    if message.from_user_id == int(current_user.get_id()):
      message_tag += f'<div id="self-message-tag-{message.id}" class="col-lg-1 offset-lg-6 col-md-1 offset-md-3 col-sm-2 offset-sm-2 col-2 offset-2">'
      if message.is_checked:
        message_tag += '<p class="text-end">既読</p>'
      message_tag += '</div>'
      message_tag += '<div class="speech-bubble-self col-lg-4 col-md-7 col-sm-6 col-6">'
      for splitted_message in replace_newline(message.message):
        message_tag += f'<p>{ urlize(splitted_message) }</p>'
      message_tag += '</div>'
      message_tag += '<div class="col-lg-1 col-md-1 col-sm-2 col-2">'
      if current_user.picture_path:
        message_tag += f'<img class="user-image-mini" src={ url_for("static", filename=current_user.picture_path) }>'
      message_tag += f'<p>{ current_user.username }</p>'
      message_tag += '</div>'
    else:
      message_tag += '<div class="col-lg-1 col-md-1 col-sm-2 col-2">'
      if user.picture_path:
        message_tag += f'<img class="user-image-mini" src={ url_for("static", filename=user.picture_path) }'
      message_tag += f'''
        <p>{ user.username }</p>
        </div>
        <div class="speech-bubble-dest col-lg-4 col-md-7 col-sm-6 col-6">
      '''
      for splitted_message in replace_newline(message.message):
        message_tag += f'<p>{ urlize(splitted_message) }<p>'
      message_tag += '''
        </div>
        <div class="col-lg-7 col-md-3 col-sm-4 col-4"></div>
      '''
  return message_tag
