import pygame
from sys import exit

pygame.init()
screen = pygame.display.set_mode((1300,580))
pygame.display.set_caption('Corre corre')
clock = pygame.time.Clock()
test_font = pygame.font.Font('Font/font.ttf', 50)

# Background
fundo = pygame.image.load('Graphics/Fundo/background_Flap.jpg').convert()
barreira = pygame.image.load('Graphics/Fundo/Barreira.jpeg').convert()
barreira = pygame.transform.scale(barreira, (110, 300)) 
barreira_rect = barreira.get_rect(bottomright = (1300,580))  # Adjusted to start within screen bounds

# Textos
Titulo = test_font.render('Meu primeiro jogo', False, 'Black')
Score = test_font.render('Score:', False, 'Black')
Score_rect = Score.get_rect(center = (770,130))

# Personagens principal
player = pygame.image.load('Graphics/Personagens/Charizard.png').convert_alpha()
player = pygame.transform.scale(player, (180, 100))    # Diminuir o tamanho da imagem
player_rect = player.get_rect(midbottom = (250,500))
player_gravidade = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.MOUSEBUTTONDOWN:   # Pula quando clica com o mouse em cima do player
            if player_rect.collidepoint(event.pos):
                player_gravidade = -14
        
        if event.type == pygame.KEYDOWN:   # Pula quando aperta o espaço
            if event.key == pygame.K_SPACE:
                player_gravidade = -14      #  Sempre que apertar subira 20 px

    screen.blit(fundo,(0,0))
    screen.blit(Titulo,(600,50))
    screen.blit(Score, Score_rect)

    barreira_rect.x -= 10
    if barreira_rect.right <= 0: 
        barreira_rect.left = 1300

    screen.blit(barreira, barreira_rect.topleft)  # Use barreira_rect for positioning

    player_gravidade += 1
    player_rect.y += player_gravidade 
    if player_rect.bottom >= 587:
        player_rect.bottom = 587

    if player_rect.top <= 0:
        player_rect.top = 0

    screen.blit(player ,player_rect)
    
    pygame.display.update()
    clock.tick(60)
