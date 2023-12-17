import socket
import time
import pygame
import random
import copy

work_on_server = True
server_ip ='localhost'
#server_ip =
server_port = 10000


# Количество кадров в секунду
FPS = 100
# Создаем комнату
WIDTH_ROMM,HEIGTH_ROMM=4000, 4000
# Создаем графическое изображение комнаты
WIDTH_SERVER_ROMM,HEIGTH_SERVER_ROMM=300, 300
START_PLAYER_SIZE=50
FOOD_SIZE=15
MOBS_QUANTITY = 25
FOOD_QUANTITY = (WIDTH_ROMM*HEIGTH_ROMM)//80000
colors={'0':(255, 255, 0), '1':(255,0,0), '2':(0, 255, 0), '3':(0,255,255), '4':(128, 0, 128)}

def new_r(R, r):
	return (R**2+r**2)**0.5

def find(s):
	otkr=None
	for i in range(len(s)):
		if s[i]=='<':
			otkr=i
		if s[i]=='>' and otkr!=None:
			zakr=i
			res=s[otkr+1:zakr]
			res=list(map(int,res.split(',')))
			return res

class Food():
	def __init__(self,x,y,r,color):
		self.x=x
		self.y=y
		self.r=r
		self.color=color

class Player():
	def __init__(self, conn, addr, x, y, r, color):
		self.conn=conn
		self.addr=addr
		self.x=x
		self.y=y
		self.r=r
		self.color=color
		self.L=1

		self.width_window = 1000
		self.height_window = 800
		self.w_vision=1000
		self.h_vision=800

		self.errors=0
		self.ready=False

		self.abs_speed = 30/(self.r**0.5)
		self.speed_x = 0
		self.speed_y = 0

	def set_options(self, data):
		data=data[1:-1].split(' ')
		self.width_window = int(data[0])
		self.height_window = int(data[1])
		self.w_vision = int(data[0])
		self.h_vision = int(data[1])



	def update(self):
		# x coordinate
		if self.x-self.r<=0:
			if self.speed_x>=0:
				self.x+=self.speed_x
		else:
			if self.x+self.r>=WIDTH_ROMM:
				if self.speed_x<=0:
					self.x+=self.speed_x
			else:
				self.x+=self.speed_x

		# y coordinate
		if self.y-self.r<=0:
			if self.speed_y>=0:
				self.y+=self.speed_y
		else:
			if self.y+self.r>=HEIGTH_ROMM:
				if self.speed_y<=0:
					self.y+=self.speed_y
			else:
				self.y+=self.speed_y

		# abs_speed
		self.abs_speed = 30/(self.r**0.5)

		# radius
		if self.r > 50:
			self.r-=self.r/5000

		# L - коэфициент маштаба
		if (self.r>=self.w_vision/5) or (self.r>=self.h_vision/5):
			if (self.w_vision<=WIDTH_ROMM) or (self.h_vision<=HEIGTH_ROMM):
				self.L*=1.5
				self.w_vision=self.width_window*self.L
				self.h_vision=self.height_window*self.L
		if (self.r<self.w_vision/8) and (self.r<self.h_vision/8):
			if self.L>1:
				self.L=self.L/1.5
				self.w_vision=self.width_window*self.L
				self.h_vision=self.height_window*self.L


	def change_speed(self, vector):
		if (vector[0]==0) and (vector[1]==0):
			self.speed_x = 0
			self.speed_y = 0
		else:
			lenv=(vector[0]**2+vector[1]**2)**0.5
			vector=(vector[0]/lenv, vector[1]/lenv)
			vector=(vector[0]*self.abs_speed, vector[1]*self.abs_speed)
			self.speed_x, self.speed_y = vector[0], vector[1]



# Создание сокета
# создаем основной socket - отвечает за подключение игроков
main_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# отключаем алгоритм Нейгла - чтобы состояния отправлялись не большими пакетами
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
# привязыем main_socket к порту компьютера
main_socket.bind((server_ip, server_port))
# чтобы socket не останавливал выполнение программы
main_socket.setblocking(0)

# ограничение на количество ОДНОВРЕМЕННО подключенных игроков
main_socket.listen(3)


# создание графического окна сервера
pygame.init()
if not work_on_server:
	screen=pygame.display.set_mode((WIDTH_SERVER_ROMM,HEIGTH_SERVER_ROMM))
clock=pygame.time.Clock()


# создание стартового набора мобов
# список всех подключений
players=[Player(None, None, random.randint(0, WIDTH_ROMM), random.randint(0, HEIGTH_ROMM), random.randint(10, 100), str(random.randint(0, 4))) for i in range(MOBS_QUANTITY)]

# создание стартового набора корма
food=[Food((random.randint(0, WIDTH_ROMM)),random.randint(0, HEIGTH_ROMM), FOOD_SIZE, str(random.randint(0, 4))) for i in range(FOOD_QUANTITY)]

table_up=[[1, 3, 3, 3, 1, 2, 3, 3, 1, 2, 2, 3, 1, 2, 3, 2], [3, 3, 3, 3, 3, 4, 3, 3, 3, 2, 4, 2, 3, 2, 2, 4], [2, 4, 3, 4, 2, 4, 2, 4, 4, 4, 3, 4, 2, 2, 2, 4], [2, 4, 4, 3, 2, 4, 4, 2, 2, 2, 4, 2, 4, 4, 4, 3]]
table_right=[[5, 4, 5, 5, 4, 3, 4, 4, 3, 2, 5, 4, 3, 2, 5, 4], [1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [3, 2, 3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 2, 2, 2, 2], [1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2]]
table_down=[[5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1], [3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3], [3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2]]
table_left=[[5, 4, 5, 5, 4, 3, 4, 4, 3, 2, 5, 4, 3, 2, 5, 4], [1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2], [3, 2, 3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 2, 2, 2, 2]]
sr_up = [0 for i in range(4)]
sr_right = [0 for i in range(4)]
sr_down = [0 for i in range(4)]
sr_left = [0 for i in range(4)]

for i in range(len(table_up)):
	sum = 0
	for j in range(len(table_up[i])):
		sum+=table_up[i][j]
	sr_up[i] = sum/len(table_up[i])

for i in range(len(table_right)):
	sum = 0
	for j in range(len(table_right[i])):
		sum+=table_right[i][j]
	sr_right[i] = sum/len(table_right[i])

for i in range(len(table_down)):
	sum = 0
	for j in range(len(table_down[i])):
		sum+=table_down[i][j]
	sr_down[i] = sum/len(table_down[i])

for i in range(len(table_left)):
	sum = 0
	for j in range(len(table_left[i])):
		sum+=table_left[i][j]
	sr_left[i] = sum/len(table_left[i])


tick=-1
server_works=True
while server_works:
	tick+=1
	clock.tick(FPS)
	# проверим, есть ли ожидающие входа в игру - возвращает адрес подключишегося игрока и выделяет ему новый socket
	if tick==200:
		tick=0
		try:
			new_socket, addr =  main_socket.accept()
			new_socket.setblocking(0)

			spawn = random.choice(food)

			new_player=Player(new_socket, addr, spawn.x, spawn.y, START_PLAYER_SIZE, str(random.randint(0, 4)))
			i_ = food.index(spawn)
			food[i_].x, food[i_].y = random.randint(0, WIDTH_ROMM), random.randint(0, HEIGTH_ROMM)

			players.append(new_player)

		except:
			pass
		# дополняем список мобов
		for i in range(MOBS_QUANTITY-len(players)):
			spawn = random.choice(food)
			players.append(Player(None, None, spawn.x, spawn.y, random.randint(10, 100), str(random.randint(0, 4))))
			i_ = food.index(spawn)
			food[i_].x, food[i_].y = random.randint(0, WIDTH_ROMM), random.randint(0, HEIGTH_ROMM)



	# считываем команды игроков
	new_list = []
	new_l = []
	for player in players:
		if (player.conn!=None) and (player.r != 0):
			try:
				data = player.conn.recv(1024)
				data=data.decode()
				if data[0]=='!': #пришло сообщение о готовности к диалогу
					player.ready=True
				else:
					if data[0]=='.' and data[-1]=='.': #пришло имя и размер окна игрока
						player.set_options(data)
						player.conn.send((str(START_PLAYER_SIZE)+' '+player.color).encode())
					else: #пришел курсор
						data=find(data)
						player.change_speed(data)
			except:
				pass
		else:
			if ((tick%100)==0) and (player.r != 0):
				#mob_coord=[[] for i in range(len(players))]
				#for i in range(len(players)):
				coord_x=0
				coord_y=0
				min_m_r, min_m_rs, min_m_i = 0, 0, 0
				min_M_r, min_M_rs, min_M_i = 0, 0, 0
				for j in range(len(players)):
					i_ = players.index(player)
					if (i_!=j):
						dist_x = players[j].x - player.x # расстояние по x
						dist_y = players[j].y - player.y # расстояние по y
						dist_r = (dist_x**2+dist_y**2)**0.5 # расстояние между центрами (длина вектора)

						if (players[j].r < player.r): # если радиус соперника меньше текущего моба
							if (min_m_r==0) or (dist_r < min_m_rs): # если записи еще нет или текущее растояние меньше предыдущих
								min_m_r=players[j].r
								min_m_rs=dist_r
								if (-dist_y<=dist_x) and (dist_x<dist_y): # если сверху
									min_m_i = 1
								else:
									if (-dist_x<dist_y) and (dist_y<=dist_x): # если справа
										min_m_i = 2
									else:
										if (-dist_y>=dist_x) and (dist_x>dist_y): # если снизу
											min_m_i = 3
										else: # если слева
											min_m_i = 4
						else: # если радиус соперника больше текущего моба
							if (min_M_r==0) or (dist_r < min_M_rs): # если записи еще нет или текущее растояние меньше предыдущих
								min_M_r=players[j].r
								min_M_rs=dist_r
								if (-dist_y<=dist_x) and (dist_x<dist_y): # если сверху
									min_M_i = 1
								else:
									if (-dist_x<dist_y) and (dist_y<=dist_x): # если справа
										min_M_i = 2
									else:
										if (-dist_y>=dist_x) and (dist_x>dist_y): # если снизу
											min_M_i = 3
										else: # если слева
											min_M_i = 4
				d = min_m_i - min_M_i #критерий (взаимное расположение меньшего и большего соседей)
				if (d<0):
					d = 4+d
				if (d==0): # 1 таблица
					#up
					new_list.clear()
					new_l.clear()
					new_list = copy.deepcopy(sr_up)
					new_l = copy.deepcopy(sr_up)
					m_max = max(new_list)
					i_max = new_list.index(max(new_list))
					new_list[i_max] = 0
					m2_max = max(new_list)
					i2_max = new_list.index(max(new_list))
					if min_m_i==0:
						if min_M_i==1:
							coord_x=0
							coord_y=new_l[1]
						else:
							if min_M_i==2:
								coord_x=new_l[2]
								coord_y=0
							else:
								if min_M_i==3:
									coord_x=new_l[0]
									coord_y=0
								else:
									coord_x=0
									coord_y=new_l[3]
					if min_m_i==1: # нет поворота
						if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
							coord_y = new_l[random.randint(0, 1)]
							if (coord_y==new_l[1]):
								coord_y=-coord_y
							coord_x=0
						else:
							if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
								coord_x = -new_l[2]
								coord_y = new_l[0]
							else:
								if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
									coord_x = new_l[3]
									coord_y = new_l[0]
								else:
									if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
										coord_x = -new_l[2]
										coord_y = -new_l[1]
									else:
										if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
											coord_x = new_l[3]
											coord_y = -new_l[1]
										else:
											coord_x = new_l[random.randint(2, 3)]
											if (coord_x==new_l[2]):
												coord_x=-coord_x
											coord_y=0
					else:
						if min_m_i==2: # поворот на 90 гр. вправо (по кругу)
							if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
								coord_y = new_l[random.randint(0, 1)]
								if (coord_x==new_l[1]):
									coord_x=-coord_x
								coord_y=0
							else:
								if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
									coord_x = new_l[0]
									coord_y = new_l[2]
								else:
									if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
										coord_x = new_l[0]
										coord_y = -new_l[3]
									else:
										if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
											coord_x = -new_l[1]
											coord_y = new_l[2]
										else:
											if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
												coord_x = -new_l[1]
												coord_y = -new_l[3]
											else:
												coord_y = new_l[random.randint(2, 3)]
												if (coord_y==new_l[3]):
													coord_y=-coord_y
												coord_x=0
						else:
							if min_m_i==3: # поворот на 180 гр. (по кругу)
								if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
									coord_y = new_l[random.randint(0, 1)]
									if (coord_y==new_l[0]):
										coord_y=-coord_y
									coord_x=0
								else:
									if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
										coord_x = new_l[2]
										coord_y = -new_l[0]
									else:
										if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
											coord_x = -new_l[3]
											coord_y = -new_l[0]
										else:
											if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
												coord_x = new_l[2]
												coord_y = new_l[1]
											else:
												if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
													coord_x = -new_l[3]
													coord_y = new_l[1]
												else:
													coord_x = new_l[random.randint(2, 3)]
													if (coord_x==new_l[3]):
														coord_x=-coord_x
													coord_y=0
							else:
								if min_m_i==4: # поворот на 90 гр. влево (по кругу)
									if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
										coord_y = new_l[random.randint(0, 1)]
										if (coord_x==new_l[0]):
											coord_x=-coord_x
										coord_y=0
									else:
										if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
											coord_x = -new_l[0]
											coord_y = -new_l[2]
										else:
											if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
												coord_x = -new_l[0]
												coord_y = new_l[3]
											else:
												if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
													coord_x = new_l[1]
													coord_y = -new_l[2]
												else:
													if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
														coord_x = new_l[1]
														coord_y = new_l[3]
													else:
														coord_y = new_l[random.randint(2, 3)]
														if (coord_y==new_l[2]):
															coord_y=-coord_y
														coord_x=0
				else:
					if(d==1):
						#left
						new_list.clear()
						new_l.clear()
						new_list = copy.deepcopy(sr_left)
						new_l = copy.deepcopy(sr_left)
						m_max = max(new_list)
						i_max = new_list.index(max(new_list))
						new_list[i_max] = 0
						m2_max = max(new_list)
						i2_max = new_list.index(max(new_list))
						if min_m_i==0:
							if min_M_i==1:
								coord_x=0
								coord_y=new_l[1]
							else:
								if min_M_i==2:
									coord_x=new_l[2]
									coord_y=0
								else:
									if min_M_i==3:
										coord_x=new_l[0]
										coord_y=0
									else:
										coord_x=0
										coord_y=new_l[3]
						if min_m_i==1: # нет поворота
							if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
								coord_y = new_l[random.randint(0, 1)]
								if (coord_y==new_l[1]):
									coord_y=-coord_y
								coord_x=0
							else:
								if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
									coord_x = -new_l[2]
									coord_y = new_l[0]
								else:
									if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
										coord_x = new_l[3]
										coord_y = new_l[0]
									else:
										if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
											coord_x = -new_l[2]
											coord_y = -new_l[1]
										else:
											if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
												coord_x = new_l[3]
												coord_y = -new_l[1]
											else:
												coord_x = new_l[random.randint(2, 3)]
												if (coord_x==new_l[2]):
													coord_x=-coord_x
												coord_y=0
						else:
							if min_m_i==2: # поворот на 90 гр. вправо (по кругу)
								if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
									coord_x = new_l[random.randint(0, 1)]
									if (coord_x==new_l[1]):
										coord_x=-coord_x
									coord_y=0
								else:
									if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
										coord_x = new_l[0]
										coord_y = new_l[2]
									else:
										if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
											coord_x = new_l[0]
											coord_y = -new_l[3]
										else:
											if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
												coord_x = -new_l[1]
												coord_y = new_l[2]
											else:
												if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
													coord_x = -new_l[1]
													coord_y = -new_l[3]
												else:
													coord_y = new_l[random.randint(2, 3)]
													if (coord_y==new_l[3]):
														coord_y=-coord_y
													coord_x=0
							else:
								if min_m_i==3: # поворот на 180 гр. (по кругу)
									if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
										coord_y = new_l[random.randint(0, 1)]
										if (coord_y==new_l[0]):
											coord_y=-coord_y
										coord_x=0
									else:
										if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
											coord_x = new_l[2]
											coord_y = -new_l[0]
										else:
											if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
												coord_x = -new_l[3]
												coord_y = -new_l[0]
											else:
												if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
													coord_x = new_l[2]
													coord_y = new_l[1]
												else:
													if ((i_max==1)) and (i2_max==3) or ((i_max==3) and (i2_max==1)):
														coord_x = -new_l[3]
														coord_y = new_l[1]
													else:
														coord_x = new_l[random.randint(2, 3)]
														if (coord_x==new_l[3]):
															coord_x=-coord_x
														coord_y=0
								else:
									if min_m_i==4: # поворот на 90 гр. влево (по кругу)
										if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
											coord_x = new_l[random.randint(0, 1)]
											if (coord_x==new_l[0]):
												coord_x=-coord_x
											coord_y=0
										else:
											if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
												coord_x = -new_l[0]
												coord_y = -new_l[2]
											else:
												if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
													coord_x = -new_l[0]
													coord_y = new_l[3]
												else:
													if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
														coord_x = new_l[1]
														coord_y = -new_l[2]
													else:
														if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
															coord_x = new_l[1]
															coord_y = new_l[3]
														else:
															coord_y = new_l[random.randint(2, 3)]
															if (coord_y==new_l[2]):
																coord_y=-coord_y
															coord_x=0
					else:
						if(d==2):
							#down
							new_list.clear()
							new_l.clear()
							new_list = copy.deepcopy(sr_down)
							new_l = copy.deepcopy(sr_down)
							m_max = max(new_list)
							i_max = new_list.index(max(new_list))
							new_list[i_max] = 0
							m2_max = max(new_list)
							i2_max = new_list.index(max(new_list))
							if min_m_i==0:
								if min_M_i==1:
									coord_x=0
									coord_y=new_l[1]
								else:
									if min_M_i==2:
										coord_x=new_l[2]
										coord_y=0
									else:
										if min_M_i==3:
											coord_x=new_l[0]
											coord_y=0
										else:
											coord_x=0
											coord_y=new_l[3]
							if min_m_i==1: # нет поворота
								if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
									coord_y = new_l[random.randint(0, 1)]
									if (coord_y==new_l[1]):
										coord_y=-coord_y
									coord_x=0
								else:
									if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
										coord_x = -new_l[2]
										coord_y = new_l[0]
									else:
										if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
											coord_x = new_l[3]
											coord_y = new_l[0]
										else:
											if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
												coord_x = -new_l[2]
												coord_y = -new_l[1]
											else:
												if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
													coord_x = new_l[3]
													coord_y = -new_l[1]
												else:
													coord_x = new_l[random.randint(2, 3)]
													if (coord_x==new_l[2]):
														coord_x=-coord_x
													coord_y=0
							else:
								if min_m_i==2: # поворот на 90 гр. вправо (по кругу)
									if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
										coord_x = new_l[random.randint(0, 1)]
										if (coord_x==new_l[1]):
											coord_x=-coord_x
										coord_y=0
									else:
										if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
											coord_x = new_l[0]
											coord_y = new_l[2]
										else:
											if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
												coord_x = new_l[0]
												coord_y = -new_l[3]
											else:
												if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
													coord_x = -new_l[1]
													coord_y = new_l[2]
												else:
													if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
														coord_x = -new_l[1]
														coord_y = -new_l[3]
													else:
														coord_y = new_l[random.randint(2, 3)]
														if (coord_y==new_l[3]):
															coord_y=-coord_y
														coord_x=0
								else:
									if min_m_i==3: # поворот на 180 гр. (по кругу)
										if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
											coord_y = new_l[random.randint(0, 1)]
											if (coord_y==new_l[0]):
												coord_y=-coord_y
											coord_x=0
										else:
											if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
												coord_x = new_l[2]
												coord_y = -new_l[0]
											else:
												if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
													coord_x = -new_l[3]
													coord_y = -new_l[0]
												else:
													if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
														coord_x = new_l[2]
														coord_y = new_l[1]
													else:
														if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
															coord_x = -new_l[3]
															coord_y = new_l[1]
														else:
															coord_x = new_l[random.randint(2, 3)]
															if (coord_x==new_l[3]):
																coord_x=-coord_x
															coord_y=0
									else:
										if min_m_i==4: # поворот на 90 гр. влево (по кругу)
											if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
												coord_x = new_l[random.randint(0, 1)]
												if (coord_x==new_l[0]):
													coord_x=-coord_x
												coord_y=0
											else:
												if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
													coord_x = -new_l[0]
													coord_y = -new_l[2]
												else:
													if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
														coord_x = -new_l[0]
														coord_y = new_l[3]
													else:
														if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
															coord_x = new_l[1]
															coord_y = -new_l[2]
														else:
															if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
																coord_x = new_l[1]
																coord_y = new_l[3]
															else:
																coord_y = new_l[random.randint(2, 3)]
																if (coord_y==new_l[2]):
																	coord_y=-coord_y
																coord_x=0
						else:
							#right
							new_list.clear()
							new_l.clear()
							new_list = copy.deepcopy(sr_right)
							new_l = copy.deepcopy(sr_right)
							m_max = max(new_list)
							i_max = new_list.index(max(new_list))
							new_list[i_max] = 0 
							m2_max = max(new_list)
							i2_max = new_list.index(max(new_list))
							if min_m_i==0:
								if min_M_i==1:
									coord_x=0
									coord_y=new_l[1]
								else:
									if min_M_i==2:
										coord_x=new_l[2]
										coord_y=0
									else:
										if min_M_i==3:
											coord_x=new_l[0]
											coord_y=0
										else:
											coord_x=0
											coord_y=new_l[3]
							if min_m_i==1: # нет поворота
								if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
									coord_y = new_l[random.randint(0, 1)]
									if (coord_y==new_l[1]):
										coord_y=-coord_y
									coord_x=0
								else:
									if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
										coord_x = -new_l[2]
										coord_y = new_l[0]
									else:
										if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
											coord_x = new_l[3]
											coord_y = new_l[0]
										else:
											if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
												coord_x = -new_l[2]
												coord_y = -new_l[1]
											else:
												if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
													coord_x = new_l[3]
													coord_y = -new_l[1]
												else:
													coord_x = new_l[random.randint(2, 3)]
													if (coord_x==new_l[2]):
														coord_x=-coord_x
													coord_y=0
							else:
								if min_m_i==2: # поворот на 90 гр. вправо (по кругу)
									if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
										coord_x = new_l[random.randint(0, 1)]
										if (coord_x==new_l[1]):
											coord_x=-coord_x
										coord_y=0
									else:
										if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
											coord_x = new_l[0]
											coord_y = new_l[2]
										else:
											if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
												coord_x = new_l[0]
												coord_y = -new_l[3]
											else:
												if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
													coord_x = -new_l[1]
													coord_y = new_l[2]
												else:
													if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
														coord_x = -new_l[1]
														coord_y = -new_l[3]
													else:
														coord_y = new_l[random.randint(2, 3)]
														if (coord_y==new_l[3]):
															coord_y=-coord_y
														coord_x=0
								else:
									if min_m_i==3: # поворот на 180 гр. (по кругу)
										if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
											coord_y = new_l[random.randint(0, 1)]
											if (coord_y==new_l[0]):
												coord_y=-coord_y
											coord_x=0
										else:
											if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
												coord_x = new_l[2]
												coord_y = -new_l[0]
											else:
												if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
													coord_x = -new_l[3]
													coord_y = -new_l[0]
												else:
													if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
														coord_x = new_l[2]
														coord_y = new_l[1]
													else:
														if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
															coord_x = -new_l[3]
															coord_y = new_l[1]
														else:
															coord_x = new_l[random.randint(2, 3)]
															if (coord_x==new_l[3]):
																coord_x=-coord_x
															coord_y=0
									else:
										if min_m_i==4: # поворот на 90 гр. влево (по кругу)
											if ((i_max==0) and (i2_max==1)) or ((i_max==1) and (i2_max==0)):
												coord_x = new_l[random.randint(0, 1)]
												if (coord_x==new_l[0]):
													coord_x=-coord_x
												coord_y=0
											else:
												if ((i_max==0) and (i2_max==2)) or ((i_max==2) and (i2_max==0)):
													coord_x = -new_l[0]
													coord_y = -new_l[2]
												else:
													if ((i_max==0) and (i2_max==3)) or ((i_max==3) and (i2_max==0)):
														coord_x = -new_l[0]
														coord_y = new_l[3]
													else:
														if ((i_max==1) and (i2_max==2)) or ((i_max==2) and (i2_max==1)):
															coord_x = new_l[1]
															coord_y = -new_l[2]
														else:
															if ((i_max==1) and (i2_max==3)) or ((i_max==3) and (i2_max==1)):
																coord_x = new_l[1]
																coord_y = new_l[3]
															else:
																coord_y = new_l[random.randint(2, 3)]
																if (coord_y==new_l[2]):
																	coord_y=-coord_y
																coord_x=0

				data=[coord_x, coord_y]
				player.change_speed(data)
		if (player.r!=0):
			player.update()


	# определим, что видит каждый игрок
	visible_balls = [[] for i in range(len(players))]
	for i in range(len(players)):
		# каких микробов видит i игрок
		for k in range(FOOD_QUANTITY):
			dist_x = food[k].x - players[i].x
			dist_y = food[k].y - players[i].y
			# i видит k
			if ((abs(dist_x)<(players[i].w_vision)//2+food[k].r) and (abs(dist_y)<(players[i].h_vision)//2+food[k].r)):
			# i может сьесть k
				if (dist_x**2 + dist_y**2 <= (players[i].r)**2):
					#изменим радиус i игрока
					players[i].r=new_r(players[i].r, food[k].r)
					food[k].x, food[k].y = random.randint(0, WIDTH_ROMM), random.randint(0, HEIGTH_ROMM)

				if (players[i].conn!=None) and (food[k].r!=0):
					# подготовим данные к добавлению в список видимых шаров
					x_=str(round(dist_x/players[i].L))
					y_=str(round(dist_y/players[i].L))
					r_=str(round(food[k].r/players[i].L))
					c_=food[k].color

					visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_)


		for j in range(i+1, len(players)):
			# рассматриваем пару i и j игрока
			dist_x = players[j].x - players[i].x
			dist_y = players[j].y - players[i].y

			# i видит j
			if ((abs(dist_x)<(players[i].w_vision)//2+players[j].r) and (abs(dist_y)<(players[i].h_vision)//2+players[j].r)):
				# i может сьесть j
				if ((dist_x**2 + dist_y**2 <= (players[i].r)**2)):
					#изменим радиус i игрока
					players[i].r=new_r(players[i].r, players[j].r)
					players[j].r, players[j].speed_x,players[j].speed_y=0,0,0



				if players[i].conn!=None:
					# подготовим данные к добавлению в список видимых шаров
					x_=str(round(dist_x/players[i].L))
					y_=str(round(dist_y/players[i].L))
					r_=str(round(players[j].r/players[i].L))
					c_=players[j].color

					visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_)

			# j видит i
			if ((abs(dist_x)<(players[j].w_vision)//2+players[i].r) and (abs(dist_y)<(players[j].h_vision)//2+players[i].r)):
				# j может сьесть i
				if ((dist_x**2 + dist_y**2 <= (players[j].r)**2)):
					#изменим радиус j игрока
					players[j].r=new_r(players[j].r, players[i].r)
					players[i].r, players[i].speed_x,players[i].speed_y=0,0,0

				if players[j].conn!=None:
					# подготовим данные к добавлению в список видимых шаров
					x_=str(round(-dist_x/players[j].L))
					y_=str(round(-dist_y/players[j].L))
					r_=str(round(players[i].r/players[j].L))
					c_=players[i].color

					visible_balls[j].append(x_+' '+y_+' '+r_+' '+c_)

	# формируем ответ каждому игроку
	otvets=['' for i in range(len(players))]
	for i in range (len(players)):
		r_ = str(round(players[i].r/players[i].L))
		visible_balls[i] = [r_] + visible_balls[i]
		otvets[i]='<'+(','.join(visible_balls[i]))+'>'


	# отправляем новое состояние игрового поля
	for i in range(len(players)):
		if (players[i].conn!=None) and (players[i].ready):
			try:
				players[i].conn.send(otvets[i].encode())
				players[i].errors=0
			except:
				players[i].errors+=1


	# чистим список от отвалившихся игроков
	for player in players:
		if (player.errors == 500) or (player.r==0):
			if player.conn!=None:
				player.conn.close()
			players.remove(player)

	if not work_on_server:
		# нарисуем состояние комнаты
		for event in pygame.event.get():
			if event.type==pygame.QUIT:
				server_works = False

		screen.fill('BLACK')
		for player in players:
			x = round(player.x*WIDTH_SERVER_ROMM/WIDTH_ROMM)
			y = round(player.y*HEIGTH_SERVER_ROMM/HEIGTH_ROMM)
			r = round(player.r*WIDTH_SERVER_ROMM/WIDTH_ROMM)
			c = colors[player.color]
			pygame.draw.circle(screen, c, (x,y), r)
		pygame.display.update()


pygame.quit()
main_socket.close()
