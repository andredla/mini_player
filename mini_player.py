#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import shutil
import uuid
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, Gtk, GLib, GdkX11, GstVideo, Gdk

from yt import YTURL
from urllib import urlopen
from urlparse import parse_qs

import time
import urllib2
#import cookielib


# http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+5%3A+GUI+toolkit+integration
h = {
"Host": "www.youtube.com",
"Accept-Language": "en-US,en;q=0.5",
"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
"DNT": "1",
"Connection": "keep-alive",
"Upgrade-Insecure-Requests": "1",
"Cache-Control": "max-age=0"
}

path = os.path.dirname(os.path.realpath(__file__))
path_folder = os.path.join(path, "mini_player_vids")
path_folder_and_file = ""
path_ico = "/usr/share/icons/" + os.popen("gsettings get org.gnome.desktop.interface icon-theme").read().strip().replace("\'", "") + "/apps/scalable/sh.svg" 

print(path_ico)

class Player(object):

	def __init__(self):
		# initialize GTK
		Gtk.init(sys.argv)

		# initialize GStreamer
		Gst.init(sys.argv)

		self.state = Gst.State.NULL
		self.duration = Gst.CLOCK_TIME_NONE
		self.playbin = Gst.ElementFactory.make("playbin", "playbin")
		self.playbin.set_property('volume', 0.5*0.5*0.5)
		if not self.playbin:
			print("ERROR: Could not create playbin.")
			sys.exit(1)

		link = self.go()

		# set up URI
		self.playbin.set_property("uri", link)

		# connect to interesting signals in playbin
		self.playbin.connect("video-tags-changed", self.on_tags_changed)
		self.playbin.connect("audio-tags-changed", self.on_tags_changed)
		self.playbin.connect("text-tags-changed", self.on_tags_changed)

		# create the GUI
		self.build_ui()

		# instruct the bus to emit signals for each received message
		# and connect to the interesting signals
		bus = self.playbin.get_bus()
		bus.add_signal_watch()
		bus.connect("message::error", self.on_error)
		bus.connect("message::eos", self.on_eos)
		bus.connect("message::state-changed", self.on_state_changed)
		bus.connect("message::application", self.on_application_message)


	def go(self):
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		texto = clipboard.wait_for_text()
		ret = texto

		if texto.find("/") < 0:
			os.system('notify-send Script "Video não encontrado..." -i '+path_ico)
			sys.exit("Erro...")

		if texto.find("http") < 0:
			ret = "file://" + texto

		if (texto.find("https") > -1 or texto.find("http") > -1) and texto.find("youtube.com") < 0:
			ret = self.url_download(texto)

		if texto.find("youtube.com") > 0:
			y = YTURL()
			vid_id = y.stripYouTubeURL(texto)
			yt_uri = "https://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en"
			#parsedResponse = parse_qs(urlopen(yt_uri % vid_id).read())
			#print(parsedResponse)
			#print( urlopen(yt_uri % vid_id).read() )

			req = urllib2.Request(yt_uri % vid_id, headers=h)
			try:
				parsedResponse = parse_qs(urllib2.urlopen(req, None, 1.0).read())
			except:
				os.system('notify-send Script "Timeout..." -i '+path_ico)
				sys.exit(1)

			ordem = []
			if len(sys.argv) > 1:
				if sys.argv[1] == "360p":
					ordem = ['18', '43', '22']
				if sys.argv[1] == "480p":
					ordem = ['135', '44', '43', '22']
				if sys.argv[1] == "720p":
					ordem = ['22', '45', '18', '43']

			availableFormats = []

			if "fmt_list" in parsedResponse:
				for fmt_list in parsedResponse["fmt_list"][0].split(','):
					print(fmt_list)

			if "url_encoded_fmt_stream_map" in parsedResponse:
				for url_encoded_fmt_stream_map in parsedResponse["url_encoded_fmt_stream_map"][0].split(','):
					vid_uri = parse_qs(url_encoded_fmt_stream_map)
					print(vid_uri)
					availableFormats.append(vid_uri)

			flag = False
			ret = availableFormats[0]["url"][0]
			for a in ordem:
				if flag == True:
					break
				for b in availableFormats:
					if b["itag"][0] == a:
						print("usando ->", b)
						ret = b["url"][0]
						flag = True
						break
					#else:
						#continue
					#break

			ret = self.url_download(ret)
		return ret

	def path_del(self):
		if os.path.exists(path_folder_and_file):
			os.remove(path_folder_and_file)
		else:
			print("Nenhum arquivo encontrado.")

		total_files_in_folder = len([name for name in os.listdir('.') if os.path.isfile(name)])
		if(total_files_in_folder <= 0):
			try:
				shutil.rmtree(path_folder)
			except:
				print("Nenhuma pasta encontrada.")
			pass

	def url_download(self, link):
		global path_folder_and_file
		req = urllib2.Request(link)
		try:
			res = urllib2.urlopen(req, None, 1.0)
			time.sleep(1)
		except:
			os.system('notify-send Script "Timeout..." -i '+path_ico)
			sys.exit(1)

		try:
			os.stat(path_folder)   			
		except:
			os.mkdir(path_folder)
		os.chdir(path_folder)

		nome = "yt_vid_"+str(uuid.uuid4())
		img = open(nome, "w")
		img.write(res.read())
		img.close()
		ext = os.popen("file -i "+nome+" | awk '{print $2}'").read().strip()
		ext = ext.split("/")[1]
		num = len(ext)-1
		ext = ext[:num]
		os.rename(nome, nome+"."+ext.lower())
		nome_ext = nome+"."+ext.lower()
		path_folder_and_file = os.path.join(path_folder, nome_ext)
		ret = "file://" + path_folder_and_file
		return ret


	# set the playbin to PLAYING (start playback), register refresh callback
	# and start the GTK main loop
	def start(self):
		# start playing
		ret = self.playbin.set_state(Gst.State.PLAYING)
		if ret == Gst.StateChangeReturn.FAILURE:
			print("ERROR: Unable to set the pipeline to the playing state")
			sys.exit(1)

		# register a function that GLib will call every second
		GLib.timeout_add_seconds(1, self.refresh_ui)

		# start the GTK main loop. we will not regain control until
		# Gtk.main_quit() is called
		Gtk.main()

		# free resources
		self.cleanup()

	# set the playbin state to NULL and remove the reference to it
	def cleanup(self):
		if self.playbin:
			self.playbin.set_state(Gst.State.NULL)
			self.playbin = None


	def click(self, widget, event):
		if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
			self.main_window.begin_move_drag(event.button, event.x_root, event.y_root, event.time)
		#pass
		if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
			widget.popup(None, None, None, None, event.button, event.time)
		return True

	def cb_quit(self, widget):
		self.on_stop(None)
		self.path_del()
		Gtk.main_quit()

	def on_volume_changed(self, widget):
		value = widget.get_value()
		value = value * value * value;
		self.playbin.set_property('volume', value)
		return True

	def on_volume_changed_btn(self, widget, vol):
		value = widget.get_value()
		value = value * value * value;
		self.playbin.set_property('volume', value)
		return True

	def build_ui(self):
		self.main_window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
		self.main_window.set_title("Minimalistic Player")
		self.main_window.set_keep_above(True)
		self.main_window.set_decorated(False)
		#self.main_window.stick()
		self.main_window.set_position(Gtk.WindowPosition.CENTER)
		self.main_window.connect("delete-event", self.on_delete_event)

		menu = Gtk.Menu()
		menu_play = Gtk.MenuItem("Play")
		menu_pause = Gtk.MenuItem("Pause")
		menu_decoration = Gtk.MenuItem("Decoration")
		menu_quit = Gtk.MenuItem("Quit")
		menu.append(menu_play)
		menu.append(menu_pause)
		menu.append(menu_decoration)
		menu.append(menu_quit)
		menu_play.show()
		menu_pause.show()
		menu_decoration.show()
		menu_quit.show()

		menu_play.connect("activate", self.on_play)
		menu_pause.connect("activate", self.on_pause)
		menu_decoration.connect("activate", self.on_decoration)
		menu_quit.connect("activate", self.cb_quit)

		video_window = Gtk.DrawingArea.new()
		video_window.set_double_buffered(False)
		video_window.connect("realize", self.on_realize)
		video_window.connect("draw", self.on_draw)

		#play_button = Gtk.Button.new_from_stock(Gtk.STOCK_MEDIA_PLAY)
		#play_button.connect("clicked", self.on_play)

		#pause_button = Gtk.Button.new_from_stock(Gtk.STOCK_MEDIA_PAUSE)
		#pause_button.connect("clicked", self.on_pause)

		#stop_button = Gtk.Button.new_from_stock(Gtk.STOCK_MEDIA_STOP)
		#stop_button.connect("clicked", self.on_stop)

		#self.volume = Gtk.HScale.new_with_range(0.0, 1.0, 0.1)
		#self.volume.set_draw_value(False)
		#self.volume.set_value(0.5)
		#self.volume.connect("value-changed", self.on_volume_changed)

		self.slider = Gtk.HScale.new_with_range(0, 100, 1)
		self.slider.set_draw_value(False)
		self.slider_update_signal_id = self.slider.connect("value-changed", self.on_slider_changed)

		self.btn_volume = Gtk.VolumeButton.new()
		self.btn_volume.set_value(0.5)
		self.btn_volume.connect("value-changed", self.on_volume_changed_btn)

		#self.streams_list = Gtk.TextView.new()
		#self.streams_list.set_editable(False)

		controls = Gtk.HBox.new(False, 0)
		#controls.pack_start(play_button, False, False, 2)
		#controls.pack_start(pause_button, False, False, 2)
		#controls.pack_start(stop_button, False, False, 2)
		controls.pack_start(self.slider, True, True, 0)
		#controls.pack_start(self.volume, True, True, 0)
		controls.pack_start(self.btn_volume, False, False, 0)

		ebox = Gtk.EventBox.new()
		ebox.connect_object("button-press-event", self.click, menu)

		main_hbox = Gtk.HBox.new(False, 0)
		main_hbox.pack_start(ebox, True, True, 0)
		ebox.add(video_window)
		#main_hbox.pack_start(video_window, True, True, 0)
		#main_hbox.pack_start(self.streams_list, False, False, 2)

		main_box = Gtk.VBox.new(False, 0)
		main_box.pack_start(main_hbox, True, True, 0)
		main_box.pack_start(controls, False, False, 0)

		#main_box.connect_object("button-press-event", self.click, menu)

		self.main_window.add(main_box)
		self.main_window.set_default_size(640, 480)
		self.main_window.show_all()

	# this function is called when the GUI toolkit creates the physical window
	# that will hold the video
	# at this point we can retrieve its handler and pass it to GStreamer
	# through the XOverlay interface
	def on_realize(self, widget):
		window = widget.get_window()
		window_handle = window.get_xid()

		# pass it to playbin, which implements XOverlay and will forward
		# it to the video sink
		self.playbin.set_window_handle(window_handle)
		# self.playbin.set_xwindow_id(window_handle)

	# this function is called when the PLAY button is clicked
	def on_play(self, button):
		self.playbin.set_state(Gst.State.PLAYING)
		pass

	# this function is called when the PAUSE button is clicked
	def on_pause(self, button):
		self.playbin.set_state(Gst.State.PAUSED)
		pass

	# this function is called when the Decoration button is clicked
	def on_decoration(self, button):
		if(self.main_window.get_decorated() == False):
			self.main_window.set_decorated(True)
		else:
			self.main_window.set_decorated(False)
		pass

	# this function is called when the STOP button is clicked
	def on_stop(self, button):
		self.playbin.set_state(Gst.State.READY)
		pass

	# this function is called when the main window is closed
	def on_delete_event(self, widget, event):
		self.on_stop(None)
		self.path_del()
		Gtk.main_quit()

	# this function is called every time the video window needs to be
	# redrawn. GStreamer takes care of this in the PAUSED and PLAYING states.
	# in the other states we simply draw a black rectangle to avoid
	# any garbage showing up
	def on_draw(self, widget, cr):
		if self.state < Gst.State.PAUSED:
			allocation = widget.get_allocation()

			cr.set_source_rgb(0, 0, 0)
			cr.rectangle(0, 0, allocation.width, allocation.height)
			cr.fill()

		return False

	# this function is called when the slider changes its position.
	# we perform a seek to the new position here
	def on_slider_changed(self, range):
		value = self.slider.get_value()
		self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, value * Gst.SECOND)


	# this function is called periodically to refresh the GUI
	def refresh_ui(self):
		current = -1

		# we do not want to update anything unless we are in the PAUSED
		# or PLAYING states
		if self.state < Gst.State.PAUSED:
			return True

		# if we don't know it yet, query the stream duration
		if self.duration == Gst.CLOCK_TIME_NONE:
			ret, self.duration = self.playbin.query_duration(Gst.Format.TIME)
			if not ret:
				print("ERROR: Could not query current duration")
			else:
				# set the range of the slider to the clip duration (in seconds)
				self.slider.set_range(0, self.duration / Gst.SECOND)

		ret, current = self.playbin.query_position(Gst.Format.TIME)
		if ret:
			# block the "value-changed" signal, so the on_slider_changed
			# callback is not called (which would trigger a seek the user
			# has not requested)
			self.slider.handler_block(self.slider_update_signal_id)

			# set the position of the slider to the current pipeline position
			# (in seconds)
			self.slider.set_value(current / Gst.SECOND)

			# enable the signal again
			self.slider.handler_unblock(self.slider_update_signal_id)

		return True

	# this function is called when new metadata is discovered in the stream
	def on_tags_changed(self, playbin, stream):
		# we are possibly in a GStreamer working thread, so we notify
		# the main thread of this event through a message in the bus
		self.playbin.post_message(Gst.Message.new_application(self.playbin, Gst.Structure.new_empty("tags-changed")))

	# this function is called when an error message is posted on the bus
	def on_error(self, bus, msg):
		err, dbg = msg.parse_error()
		print("ERROR:", msg.src.get_name(), ":", err.message)
		if dbg:
			print("Debug info:", dbg)

	# this function is called when an End-Of-Stream message is posted on the bus
	# we just set the pipeline to READY (which stops playback)
	def on_eos(self, bus, msg):
		print("End-Of-Stream reached")
		self.playbin.set_state(Gst.State.READY)

	# this function is called when the pipeline changes states.
	# we use it to keep track of the current state
	def on_state_changed(self, bus, msg):
		old, new, pending = msg.parse_state_changed()
		if not msg.src == self.playbin:
			# not from the playbin, ignore
			return

		self.state = new
		print("State changed from {0} to {1}".format(
		Gst.Element.state_get_name(old), Gst.Element.state_get_name(new)))

		if old == Gst.State.READY and new == Gst.State.PAUSED:
			# for extra responsiveness we refresh the GUI as soons as
			# we reach the PAUSED state
			self.refresh_ui()

	# extract metadata from all the streams and write it to the text widget
	# in the GUI
	def analyze_streams(self):
		# clear current contents of the widget
		buffer = self.streams_list.get_buffer()
		buffer.set_text("")

		# read some properties
		nr_video = self.playbin.get_property("n-video")
		nr_audio = self.playbin.get_property("n-audio")
		nr_text = self.playbin.get_property("n-text")

		for i in range(nr_video):
			tags = None
			# retrieve the stream's video tags
			tags = self.playbin.emit("get-video-tags", i)
			if tags:
				buffer.insert_at_cursor("video stream {0}\n".format(i))
				_, str = tags.get_string(Gst.TAG_VIDEO_CODEC)
				buffer.insert_at_cursor(
				"  codec: {0}\n".format(
				str or "unknown"))

		for i in range(nr_audio):
			tags = None
			# retrieve the stream's audio tags
			tags = self.playbin.emit("get-audio-tags", i)
			if tags:
				buffer.insert_at_cursor("\naudio stream {0}\n".format(i))
				ret, str = tags.get_string(Gst.TAG_AUDIO_CODEC)
				if ret:
					buffer.insert_at_cursor(
					"  codec: {0}\n".format(
					str or "unknown"))

				ret, str = tags.get_string(Gst.TAG_LANGUAGE_CODE)
				if ret:
					buffer.insert_at_cursor(
					"  language: {0}\n".format(
					str or "unknown"))

				ret, str = tags.get_uint(Gst.TAG_BITRATE)
				if ret:
					buffer.insert_at_cursor(
					"  bitrate: {0}\n".format(
					str or "unknown"))

		for i in range(nr_text):
			tags = None
			# retrieve the stream's subtitle tags
			tags = self.playbin.emit("get-text-tags", i)
			if tags:
				buffer.insert_at_cursor("\nsubtitle stream {0}\n".format(i))
				ret, str = tags.get_string(Gst.TAG_LANGUAGE_CODE)
				if ret:
					buffer.insert_at_cursor(
					"  language: {0}\n".format(
					str or "unknown"))

	# this function is called when an "application" message is posted on the bus
	# here we retrieve the message posted by the on_tags_changed callback
	def on_application_message(self, bus, msg):
		if msg.get_structure().get_name() == "tags-changed":
			# if the message is the "tags-changed", update the stream info in
			# the GUI
			#self.analyze_streams()
			pass

if __name__ == '__main__':
	p = Player()
	p.start()
