import discord
import pytube as pt
import os 
import string
import random
import threading
import dotenv
import time
import multiprocessing


dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
#set os path
path = os.getcwd()





class LofiClient(discord.Client):
    def __init__(self, urls, files_hold, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for arg in args:
            print( arg)
        self.counter = []
        self.urls = urls
        self.files_hold = files_hold
        self.proccesses = []
        self.active_vcs = []
        self.servers_playing = []
        self.proccess_events = []
        self.proccess_managers = []
        #self.manager = multiprocessing.Manager()
    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
    async def on_message(self, message):
        if message.content.startswith('#play'):
            if message.guild.id not in self.servers_playing:
                
                self.servers_playing.append(message.guild.id)
                index = self.servers_playing.index(message.guild.id)
                self.counter.append(0)

                await message.channel.send('Playing')
                self.active_vcs.append(await message.author.voice.channel.connect())
                #check if count is less than len(urls)
                if self.counter[index] > len(self.urls):
                    self.counter[index] = 0
                self.proccess_events.append(multiprocessing.Event())
                self.proccess_managers.append(multiprocessing.Queue())
                
                #creat new proccess to loop songs
                self.proccesses.append(multiprocessing.Process(target=loop_songs, args=(self.proccess_events[index], self.proccess_managers[index], self.counter[index], self.active_vcs[index], self.urls, self.files_hold)))
                self.proccesses[index].start() 
        if message.content.startswith('#stop'):
            if message.guild.id in self.servers_playing:
                index = self.servers_playing.index(message.guild.id)
                self.proccess_events[index].set()
                self.proccesses[index].join()
                await self.active_vcs[index].disconnect()
                await message.channel.send('Stopped')
                self.servers_playing.pop(index)
                self.counter.pop(index)
                self.active_vcs.pop(index)
                self.proccess_events.pop(index)
                self.proccess_managers.pop(index)
                self.proccesses.pop(index)
        if message.content.startswith('#skip'):
            if message.guild.id in self.servers_playing:
                index = self.servers_playing.index(message.guild.id)
                self.proccess_events[index].set()
                self.counter[index] = self.proccess_managers[index].get()
                self.proccesses[index].join()

                
                self.proccess_events[index].clear()
                self.proccess_managers[index] = multiprocessing.Queue()
                
                print('value after counter')
                
                
                await message.channel.send('Skipped')
                if self.counter[index] > len(self.urls):
                    self.counter[index] = 0
                
                self.proccesses[index] = multiprocessing.Process(target=loop_songs, args=(self.proccess_events[index], self.proccess_managers[index], self.counter[index], self.active_vcs[index], self.urls, self.files_hold))
                self.proccesses[index].start()
        if message.content.startswith('#add'):
            letters = string.ascii_lowercase
            f = open(path + 'urls.txt', 'a')
            f.write(message.content[5:] + '\n')
            f.close()
            self.urls.append(message.content[5:])
            self.files_hold.append(''.join(random.choice(letters) for i in range(10)))
            await message.channel.send('Added')
        if message.content.startswith('#remove'):
            remove_index = int(message.content[8:].replace(' ', ''))
             
            
            f = open(path + 'urls.txt', 'r')
            lines = f.readlines()
            f.close()
            f = open(path + 'urls.txt', 'w')
            for line in lines:
                if line != self.urls[remove_index] + '\n':
                    f.write(line)
            f.close()
            self.urls.pop(remove_index)
            
            await message.channel.send('Removed')
        if message.content.startswith('#list'):
            await message.channel.send('Current songs in lists (to remove a song \'#remove x\', x being the number beside link):')
            for x in range(len(self.urls)):
                await message.channel.send(f'{x}: {self.urls[x]}')




def get_songs(index, urls, files_hold):
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
    

def loop_songs(e, d, starts, vc, urls, files_hold):
    event = e
    first = True
    count = starts
    print('loop count')
    print(count)
    print('d')
    print(d)
    
    while event.is_set() == False:
        
        if count >= len(urls):
            count = 0
        if first == True:
            url = get_songs(count, urls, files_hold)
            first = False
        
        t1 = threading.Thread(target=play_song, args=(url, vc, ))
        t1.start()
        url = get_songs(count, urls, files_hold)
        
        while t1.is_alive():

            time.sleep(2)
            if event.is_set() != False:
                print('event set')
                t1.do_run = False
        t1.join()
        count += 1
        d.put( count)
    
    
def main():
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
    client = LofiClient(urls, files_hold)
    client.run(TOKEN)

if __name__ == '__main__':
    main()
       

#class MyClient(discord.Client):
#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)
#        self.counter = 0
#        self.current = ""
#        self.t = ""
#        self.vc_hold = ""
#        
#    async def on_ready(self):
#        print('Logged on as {0}!'.format(self.user))
#        print('We are on the following servers:')
#        for guild in self.guilds:
#            print('{0.name}({0.id})'.format(guild))
#        self.current = get_songs(0)
#        self.counter += 1
#
#    async def on_message(self, message):
#        if message.author == self.user:
#            return
#
#        if message.content.startswith('#help'):
#            await message.channel.send('To start the bot type #start \n To stop the bot type #stop \n To add songs type #add <url> \n To remove songs type #remove <index> \n To get index of all songs type #list')
#        if message.content.startswith('#play'):
#            await message.channel.send('Playing')
#            self.vc_hold = await message.author.voice.channel.connect()
#            
#            #check if count is less than len(urls)
#            if self.counter > len(urls):
#                self.counter = 0
#            
#            #creat new thread to download song
#            self.t = threading.Thread(target=loop_songs, args=(self.counter, self.vc_hold, self.current, ))
#            self.t.start()
#        if message.content.startswith('#add'):
#            f = open(path + 'urls.txt', 'a')
#            f.write(message.content[5:] + '\n')
#            f.close()
#            urls.append(message.content[5:])
#            files_hold.append(''.join(random.choice(letters) for i in range(10)))
#            await message.channel.send('Added')
#        if message.content.startswith('#remove'):
#            remove_index = int(message.content[8:].replace(' ', ''))
#             
#            
#            f = open(path + 'urls.txt', 'r')
#            lines = f.readlines()
#            f.close()
#            f = open(path + 'urls.txt', 'w')
#            for line in lines:
#                if line != urls[remove_index] + '\n':
#                    f.write(line)
#            f.close()
#            urls.pop(remove_index)
#            
#            await message.channel.send('Removed')
#        if message.content.startswith('#stop'):
#            if self.t != "":
#                self.t.do_run = False
#                self.t.join()
#                self.t = ""
#            await self.vc_hold.disconnect()
#            await message.channel.send('Stopped')
#            self.vc_hold = ""
#        if message.content.startswith('#list'):
#            await message.channel.send('Current songs in lists (to remove a song \'#remove x\', x being the number beside link):')
#            for x in range (len(urls)):
#                await message.channel.send(f'{x}: {urls[x]}')


