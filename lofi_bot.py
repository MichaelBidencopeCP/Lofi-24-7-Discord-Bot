import discord
import pytube as pt
import os
import string
import random
import threading
import dotenv


dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
#set os path

path = os.getcwd()
print(path)
letters = string.ascii_lowercase
urls = []
files_hold = []
current_song_path = ""
f = open(path + '/urls.txt', 'r')
for line in f:
    urls.append(line)
    x = ''.join(random.choice(letters) for i in range(10))
    while x in files_hold:
        x = ''.join(random.choice(letters) for i in range(10))
    files_hold.append(x)
f.close()

def get_songs(index):
    yt = pt.YouTube(urls[index])
    t = yt.streams.filter(only_audio=True)
    print(t[0].default_filename[-4:])
    current_song_path = t[0].download(output_path= path + '/files', filename = files_hold[index] + t[0].default_filename[-4:]) 
    return current_song_path

def play_song(cur, vc):
    

    vc.play(discord.FFmpegPCMAudio(source=cur))
    while vc.is_playing():
        pass
    stop_song(vc, cur)

def stop_song(vc, cur):
    vc.stop()
    
    os.remove(cur)
    print('deleted')

def loop_songs(start, vc, current):
    ct = threading.currentThread()
    
    cur = current
    count = start
    while getattr(ct, "do_run", True):
        if count >= len(urls):
            count = 0
        t1 = threading.Thread(target=play_song, args=(cur, vc, ))
        t1.start()
        cur = get_songs(count) 
        t1.join()
        count += 1
    stop_song(vc, current)
        

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.current = ""
        self.t = ""
        
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        print('We are on the following servers:')
        for guild in self.guilds:
            print('{0.name}({0.id})'.format(guild))
        self.current = get_songs(0)
        self.counter += 1

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('#hello'):
            await message.channel.send('Hello World!')
        if message.content.startswith('#play'):
            await message.channel.send('Playing')
            vc = await message.author.voice.channel.connect()
            #check if count is less than len(urls)
            if self.counter > len(urls):
                self.counter = 0
            
            #creat new thread to download song
            self.t = threading.Thread(target=loop_songs, args=(self.counter, vc, self.current, ))
            self.t.start()
        if message.content.startswith('#add'):
            f = open(path + 'urls.txt', 'a')
            f.write(message.content[5:] + '\n')
            f.close()
            urls.append(message.content[5:])
            files_hold.append(''.join(random.choice(letters) for i in range(10)))
            await message.channel.send('Added')
        if message.content.startswith('#remove'):
            f = open(path + 'urls.txt', 'r')
            lines = f.readlines()
            f.close()
            f = open(path + 'urls.txt', 'w')
            for line in lines:
                if line != message.content[8:] + '\n':
                    f.write(line)
            f.close()
            urls.remove(message.content[8:])
            await message.channel.send('Removed')
        if message.content.startswith('#stop'):
            if self.t != "":
                self.t.do_run = False
                self.t.join()
                self.t = ""
        if message.content.startswith('#list'):
            await message.channel.send(urls)
        

client = MyClient()
client.run(TOKEN)