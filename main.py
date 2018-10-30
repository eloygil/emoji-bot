import io
import os
import sys
import uuid
import numpy as np
import random
import telebot
import requests
import traceback
import subprocess
import argparse
from precompute import get_precomputed_dict
from scipy import misc
from scipy.spatial import KDTree
from img2emoji import img2emoji

def parse_arguments():
  '''Parse command line arguments
  '''
  parser = argparse.ArgumentParser(
    description = 'A Telegram Bot that converts images to emoji art'
  )
  parser.add_argument('TOKEN', help = 'Bot Token (see Telegram BotFather if you do not know what is this')
  parser.add_argument('--emoji_resolution', type = int, default = 9,
  help = 'Emoji resolution. See resources folder to see available resolutions')
  parser.add_argument('--force_precompute', action = 'store_true',
  help = 'Recompute the dictionaries and the KDTree')
  return parser.parse_args()

def main(TOKEN, emoji_resolution, force_precompute):
  '''Main procedure.
  Compute all the emoji related stuff (or retrieve it if possible), and
  run the main bot loop (polling).
  '''
  # load the emojis and store them in a dict of the form {mean : image}
  image_dict = get_precomputed_dict('emojis%d' % emoji_resolution,
  force_precompute)
  image_points = np.array([list(p) for p in image_dict.keys()])
  search_tree = KDTree(image_points)
  emoji_height, emoji_width, _ = image_dict[tuple(image_points[0])].shape

  # initialize the bot
  bot = telebot.TeleBot(TOKEN)

  # BOT METHODS

  @bot.message_handler(commands=['help', 'start'])
  def help(msg):
    '''Help command.
    '''
    bot.send_message(msg.chat.id, 'I convert images to emoji art. Send me a picture!')

  def python_interpreter():
    import sys
    return 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)

  @bot.message_handler(content_types=['photo'])
  def handle_images(message):
    '''Given a photo, tries to create an emoji-art image from it.
    If not possible, then a simple message will be displayed instead.
    '''
    try:
      # read the image and put it in a np.ndarray
      photo = message.photo[-1]
      image_file_path = bot.get_file(photo.file_id).file_path
      local_file_path = os.path.join(os.path.split(sys.argv[0])[0], '%s.png'%str(uuid.uuid4()))
      image_file = bot.download_file(image_file_path)
      f = io.BytesIO(image_file)
      image_content = misc.imread(f)
      # get the emoji-art image
      ret = img2emoji(image_content, image_dict, search_tree)
      # save the image in png format, then send it
      misc.imsave(local_file_path, ret)
      send_image = open(local_file_path, 'rb')
      bot.send_photo(message.chat.id, send_image)
      subprocess.Popen([python_interpreter(), 'file_deleter.py', local_file_path])
    except:
      # I decided to leave this generic except instead of handling more specific
      # cases
      # because the code above can fail for many reasons, but the way to do
      # is the same in all cases
      traceback.print_exc()
      bot.reply_to(message, 'Something went wrong. Sorry :(')

  bot.polling()

if __name__ == "__main__":
  opts = parse_arguments()
  main(**vars(opts))
