import socket
import pygame

# ширина и высота игрового поля
WIDTH_WINDOW, HEIGHT_WINDOW = 1000, 800

colors={'0':(255, 255, 0), '1':(255,0,0), '2':(0, 255, 0), '3':(0,255,255), '4':(128, 0, 128)}



def find(s):
	otkr=None
	for i in range(len(s)):
		if s[i]=='<':
			otkr=i
		if s[i]=='>' and otkr!=None:
			zakr=i
			res=s[otkr+1:zakr]
			return res
	return ''

def draw_opponents(data):
	for i in range(len(data)):
		j = data[i].split(' ')

		x=WIDTH_WINDOW//2+int(j[0])
		y=HEIGHT_WINDOW//2+int(j[1])
		r=int(j[2])
		c = colors[j[3]]
		pygame.draw.circle(screen,c,(x,y),r)

class Me():
	def __init__(self, data):
		data=data.split()
		self.r=int(data[0])
		self.color=data[1]

	def update(self, new_r):
		self.r=new_r

	def draw(self):
		if self.r!=0:
			pygame.draw.circle(screen, colors[self.color], (WIDTH_WINDOW//2, HEIGHT_WINDOW//2), self.r)


# подключение к серверу
try:
	# создаем socket - отвечает за подключение игрока к серверу
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# отключаем алгоритм Нейгла - чтобы состояния отправлялись не большими пакетами
	sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	sock.connect(('localhost', 10000))

	#my_name = 'Лиза'
	# отправляем серверу размеры окна
	#sock.send(('.'+my_name+' '+str(WIDTH_WINDOW)+' '+ str(HEIGHT_WINDOW)+'.').encode())
	sock.send(('.'+str(WIDTH_WINDOW)+' '+ str(HEIGHT_WINDOW)+'.').encode())
except:
	error = True


# получаем свой размер и цвет
try:
	data = sock.recv(64).decode()
	error = False
	# подтверждаем получение
	sock.send('!'.encode())

	data1=data.split()
	if (data!=['']) and (len(data1)>=2):
		me = Me(data)
	else:
		error = True
except:
	error = True




# создание окна игры
pygame.init()
screen=pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption('Agario')


vector = (0,0)
old_vector = (0,0)
running = True
#error = True 
#clock=pygame.time.Clock()
#tick = 0
while running:
	#tick+=1
	#clock.tick(1)
	if (error==False):
		# обработка событий
		for event in pygame.event.get():
			if event.type==pygame.QUIT:
				running = False

		# считаем положение мыши
		if pygame.mouse.get_focused():
			pos=pygame.mouse.get_pos()
			vector=(pos[0]-WIDTH_WINDOW//2, pos[1]-HEIGHT_WINDOW//2)

			if ((vector[0])**2+(vector[1])**2 <= me.r**2):
				vector=(0,0)


		# отправляем команду на сервер
		if vector!=old_vector:
			old_vector = vector
			message='<' + str(vector[0]) + ',' + str(vector[1]) + '>'
			try:
				sock.send(message.encode())
			except:
				running = False
				continue

		# получаем от сервера новое состояние игрового поля
		try:
			data=sock.recv(2**20)
		except:
			running = False
			continue
		data=data.decode()
		data=find(data)
		data=data.split(',')


		# рисуем новое состояние игрового поля
		# фон поля
		screen.fill('gray25')
		# рисуем оппонентов
		if data!=['']:
			me.update(int(data[0]))
			draw_opponents(data[1:])
			me.draw()
		# обновляем экран
		pygame.display.update()
	else:
		running = False
		#fonto = pygame.font.Font(None, 50)
		#text = fonto.render('Сервер не отправил данные!', True, 'gray25', (255, 0, 0))
		#rect = text.get_rect(center=(WIDTH_WINDOW//2, HEIGHT_WINDOW//2))
		#screen.blit(text, rect)
		#screen.fill('BLACK')
		#f1 = pygame.font.Font(None, 36)
		#text1 = f1.render('Сервер не отправил данные!', 1, (255, 0, 0))
		# обновляем экран
		#pygame.display.flip()
		#clock.tick(200)
		#if (tick==20):
		#	running = False
pygame.quit() 
