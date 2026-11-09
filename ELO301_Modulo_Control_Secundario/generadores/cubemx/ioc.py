"""Escribe ELO301_G1.ioc (STM32CubeMX) con la asignación de pines de la Tabla 9 del documento, revisión 1.4.

Las etiquetas son las de las figuras de la revisión 1.3; cambian LED_HB (PB6 -> PB9) y se agrega la USART1 de
depuración (DBG_TX en PB6, DBG_RX en PB7). CubeMX completa el resto con sus valores por defecto al abrirlo.
Uso: python3 ioc.py  -> ELO301_G1.ioc junto a este archivo
"""
import os

# pin: (señal, modo o None, etiqueta)
PINES = {
    'PF0-OSC_IN': ('RCC_OSC_IN', 'HSE-External-Oscillator', None), 'PF1-OSC_OUT': ('RCC_OSC_OUT', 'HSE-External-Oscillator', None),
    'PA13': ('SYS_JTMS-SWDIO', 'Serial_Wire', None), 'PA14': ('SYS_JTCK-SWCLK', 'Serial_Wire', None),
    'PA0': ('S_TIM2_CH1', None, 'GNSS_PPS'), 'PA1': ('ADC1_IN2', 'IN2-Single-Ended', 'VIN_SENSE'),
    'PA2': ('USART2_TX', 'Asynchronous', 'GNSS_RX'), 'PA3': ('USART2_RX', 'Asynchronous', 'GNSS_TX'),
    'PA4': ('GPIO_Output', None, 'IMU_CS'), 'PA5': ('SPI1_SCK', 'Full_Duplex_Master', 'IMU_SCK'),
    'PA6': ('SPI1_MISO', 'Full_Duplex_Master', 'IMU_MISO'), 'PA7': ('SPI1_MOSI', 'Full_Duplex_Master', 'IMU_MOSI'),
    'PB0': ('GPXTI0', None, 'IMU_INT1'), 'PB1': ('GPIO_Output', None, 'FOC_CS1'), 'PB2': ('GPIO_Output', None, 'FOC_CS2'),
    'PB10': ('GPIO_Output', None, 'FOC_CS3'), 'PB11': ('GPIO_Output', None, 'FOC_CS4'),
    'PB13': ('SPI2_SCK', 'Full_Duplex_Master', 'FOC_SCK'), 'PB14': ('SPI2_MISO', 'Full_Duplex_Master', 'FOC_MISO'),
    'PB15': ('SPI2_MOSI', 'Full_Duplex_Master', 'FOC_MOSI'),
    'PA8': ('I2C2_SDA', 'I2C', 'TOF_SDA'), 'PA9': ('I2C2_SCL', 'I2C', 'TOF_SCL'), 'PA10': ('GPIO_Output', None, 'SUP_IRQ'),
    'PA15': ('SPI3_NSS', 'NSS_Signal_Hard_Input', 'SUP_NSS'), 'PB3': ('SPI3_SCK', 'Full_Duplex_Slave', 'SUP_SCK'),
    'PB4': ('SPI3_MISO', 'Full_Duplex_Slave', 'SUP_MISO'), 'PB5': ('SPI3_MOSI', 'Full_Duplex_Slave', 'SUP_MOSI'),
    'PB6': ('USART1_TX', 'Asynchronous', 'DBG_TX'), 'PB7': ('USART1_RX', 'Asynchronous', 'DBG_RX'),
    'PB9': ('GPIO_Output', None, 'LED_HB'),
}
IPS = ['ADC1', 'I2C2', 'NVIC', 'RCC', 'SPI1', 'SPI2', 'SPI3', 'SYS', 'TIM2', 'USART1', 'USART2']
EXTRA = """NVIC.EXTI0_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:true\\:true\\:true
RCC.HSE_VALUE=25000000
RCC.IPParameters=HSE_VALUE
SH.GPXTI0.0=GPIO_EXTI0
SH.GPXTI0.ConfNb=1
SH.S_TIM2_CH1.0=TIM2_CH1,Input_Capture1_from_TI1
SH.S_TIM2_CH1.ConfNb=1
SPI1.Direction=SPI_DIRECTION_2LINES
SPI1.IPParameters=VirtualType,Mode,Direction
SPI1.Mode=SPI_MODE_MASTER
SPI1.VirtualType=VM_MASTER
SPI2.Direction=SPI_DIRECTION_2LINES
SPI2.IPParameters=VirtualType,Mode,Direction
SPI2.Mode=SPI_MODE_MASTER
SPI2.VirtualType=VM_MASTER
SPI3.Direction=SPI_DIRECTION_2LINES
SPI3.IPParameters=VirtualType,Mode,Direction,VirtualNSS
SPI3.Mode=SPI_MODE_SLAVE
SPI3.VirtualNSS=VM_NSSHARD
SPI3.VirtualType=VM_SLAVE
TIM2.Channel-Input_Capture1_from_TI1=TIM_CHANNEL_1
TIM2.IPParameters=Channel-Input_Capture1_from_TI1
USART1.IPParameters=VirtualMode-Asynchronous
USART1.VirtualMode-Asynchronous=VM_ASYNC
USART2.IPParameters=VirtualMode-Asynchronous
USART2.VirtualMode-Asynchronous=VM_ASYNC
VP_SYS_VS_Systick.Mode=SysTick
VP_SYS_VS_Systick.Signal=SYS_VS_Systick
board=custom
"""

if __name__ == '__main__':
    pines = list(PINES) + ['VP_SYS_VS_Systick']
    l = ['#MicroXplorer Configuration settings - do not modify', 'File.Version=6', 'GPIO.groupedBy=Group By Peripherals',
         'KeepUserPlacement=false', 'Mcu.CPN=STM32G431CBT6', 'Mcu.Family=STM32G4']
    l += [f'Mcu.IP{i}={ip}' for i, ip in enumerate(IPS)] + [f'Mcu.IPNb={len(IPS)}', 'Mcu.Name=STM32G431C(6-8-B)Tx', 'Mcu.Package=LQFP48']
    l += [f'Mcu.Pin{i}={p}' for i, p in enumerate(pines)] + [f'Mcu.PinsNb={len(pines)}', 'Mcu.ThirdPartyNb=0', 'Mcu.UserConstants=',
                                                           'Mcu.UserName=STM32G431CBTx', 'MxCube.Version=6.18.1', 'MxDb.Version=DB.6.0.181']
    for p, (sen, modo, eti) in PINES.items():
        if eti: l += [f'{p}.GPIOParameters=GPIO_Label', f'{p}.GPIO_Label={eti}']
        if sen.startswith(('GPIO', 'GPXTI')) or p == 'PA15': l.append(f'{p}.Locked=true')  # chinche como en la rev. 1.3
        if modo: l.append(f'{p}.Mode={modo}')
        l.append(f'{p}.Signal={sen}')
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ELO301_G1.ioc')
    _ = open(salida, 'w', newline='\n').write('\n'.join([l[0]] + sorted(l[1:] + EXTRA.strip().split('\n'))) + '\n')
    print(salida, len(PINES), 'pines')
