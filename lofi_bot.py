import discord
import pytube as pt
import os 
import string
import random
import threading
import dotenv
import time


dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
#set os path
path = os.getcwd()

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
    current_song_path = t[0].download(output_path= path + '/files', filename = files_hold[index] + t[0].default_filename[-4:]) 
    return current_song_path

def play_song(cur, vc):
    th = threading.currentThread()


    vc.play(discord.FFmpegPCMAudio(source=cur))
    while vc.is_playing() and getattr(th, "do_run", True):
        pass

    vc.stop()
    
    
    os.remove(cur)
    

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
        
        while t1.is_alive():
            
            ct = threading.currentThread()
            time.sleep(2)
            if not getattr(ct, "do_run", True):
                
                
                t1.do_run = False
                
        t1.join()
        count += 1
    
    
        

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.current = ""
        self.t = ""
        self.vc_hold = ""
        
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

        if message.content.startswith('#help'):
            await message.channel.send('To start the bot type #start \n To stop the bot type #stop \n To add songs type #add <url> \n To remove songs type #remove <index> \n To get index of all songs type #list')
        if message.content.startswith('#play'):
            await message.channel.send('Playing')
            self.vc_hold = await message.author.voice.channel.connect()
            
            #check if count is less than len(urls)
            if self.counter > len(urls):
                self.counter = 0
            
            #creat new thread to download song
            self.t = threading.Thread(target=loop_songs, args=(self.counter, self.vc_hold, self.current, ))
            self.t.start()
        if message.content.startswith('#add'):
            f = open(path + 'urls.txt', 'a')
            f.write(message.content[5:] + '\n')
            f.close()
            urls.append(message.content[5:])
            files_hold.append(''.join(random.choice(letters) for i in range(10)))
            await message.channel.send('Added')
        if message.content.startswith('#remove'):
            remove_index = int(message.content[8:].replace(' ', ''))
             
            
            f = open(path + 'urls.txt', 'r')
            lines = f.readlines()
            f.close()
            f = open(path + 'urls.txt', 'w')
            for line in lines:
                if line != urls[remove_index] + '\n':
                    f.write(line)
            f.close()
            urls.pop(remove_index)
            
            await message.channel.send('Removed')
        if message.content.startswith('#stop'):
            if self.t != "":
                self.t.do_run = False
                self.t.join()
                self.t = ""
            await self.vc_hold.disconnect()
            await message.channel.send('Stopped')
            self.vc_hold = ""
        if message.content.startswith('#list'):
            await message.channel.send('Current songs in lists (to remove a song \'#remove x\', x being the number beside link):')
            for x in range (len(urls)):
                await message.channel.send(f'{x}: {urls[x]}')

client = MyClient()
client.run(TOKEN)