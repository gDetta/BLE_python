import asyncio
from bleak import BleakScanner, BleakClient



async def on_connection(client : BleakClient):
    """
    Connection callback
    """
            
    while True:

        #=========================================================
        # User commands
        #=========================================================
        command = input('Enter a command (quit, list_ser, read_name, serial_over_ble): ').lower()


        if command == 'quit':
            break


        elif command == 'list_ser':
            # services = await client.get_services()
            services = client.services
            for service in services:
                print(f'Service: {service.uuid}, description: {service.description}')
                for char in service.characteristics:
                    print(f'  Characteristic: {char.uuid}, description: {char.description}, properties: {char.properties}')


        elif command == "read_name":
            CHAR_NAME = "00002a00-0000-1000-8000-00805f9b34fb"
            try:
                value = await client.read_gatt_char(CHAR_NAME)  # bytearray
                print(f'Name: {value.decode('utf-8')}')
            except Exception as e:
                print(f'Error reading characteristic: {e}')


        elif command == "serial_over_ble":
            READ_NOTIFY_CHAR_UUID = "0003cdd1-0000-1000-8000-00805f9b0131"  # Rx characteristic 
            WRITE_CHAR_UUID = "0003cdd2-0000-1000-8000-00805f9b0131"        # Tx characteristic 

            #  Subscribe to notifications (to receive data)
            def notification_handler(sender, data):
                print(f"Received: {data.hex()}")    # Received as bytearray and converted to hex
            await client.start_notify(READ_NOTIFY_CHAR_UUID, notification_handler)


            # Send data (write to BLE serial)
            data_to_send = "a53200f907" # hex data
            data_bytearray = bytearray.fromhex(data_to_send)
            await client.write_gatt_char(WRITE_CHAR_UUID, data_bytearray )  # as bytearray
            print(f"Sent: {data_bytearray.hex()}")


            # Keep the connection open for testing
            await asyncio.sleep(10)  


        else:
            print('Unknown command. Use list, read <uuid>, or quit.')



def on_disconnect(client):
        """
        Disconnection callback
        """
        print("\nDevice disconnected")



async def scan_and_connect():

    #=======================================================
    # Scan
    #=======================================================
    print('Scanning for Bluetooth devices...')

    # Dizionario con chiave mac_addr (str) e valore tupla con oggetti (BLEDevice, AdvertisementData)
    # devices_dict = {
    #     "addr1": (device1, advData1),
    #     "addr2": (device2, advData2),
    # }
    # Can be accessed as:
    # devices, advData = [devices, advData for addresses, (devices, advData) in devices_dict.items()]
    devices_dict = await BleakScanner.discover(return_adv=True)


    #=======================================================
    # Select device
    #=======================================================
    # Create a sub dictionary with only user devices
    user_devices_dict = {address : (device, advData) for address, (device, advData) in devices_dict.items() if str(device.name).startswith("xxxx") }
    
    # Create a list of tuples, sorted by Power signal (RSSI) in descending order
    user_list_tuple = [(device, advData) for (device, advData) in user_devices_dict.values()]
    user_list_sorted_tuple = sorted(user_list_tuple, key=lambda x: x[1].rssi, reverse=True)
    
    # Check how many users are present
    user_found = len(user_list_sorted_tuple)

    # Select user
    selected_user_tuple = None
    # Only 1 user
    if user_found == 1:
        selected_user_tuple = user_list_sorted_tuple[0]
        print(f"\nOnly 1 user found, connect automatically to:")
        print(f'Name: {selected_user_tuple[0].name or 'Unknown'}, Address: {selected_user_tuple[0].address}, RSSI: {selected_user_tuple[1].rssi} dBm')
    # More users: User selection
    else:
        print('Found users:')
        for i, (device, advData) in enumerate(user_list_sorted_tuple):
            print(f'{i+1}. Name: {device.name or 'Unknown'}, Address: {device.address}, RSSI: {advData.rssi} dBm')
        # User select device
        user_choice = int(input('Enter the number of the device you want to connect to: ')) - 1
        selected_user_tuple = user_list_sorted_tuple[user_choice]

    

    #=======================================================
    # Connection
    #=======================================================
    print(f'\nConnecting to {selected_user_tuple[0].name}...')



    async with BleakClient(selected_user_tuple[0], disconnected_callback=on_disconnect) as client:

        # Connected
        if client.is_connected:
            print( f'Connected to {selected_user_tuple[0].name or 'Unknown device'}')

            await on_connection(client)


        else:
            print('Failed to connect')






#===============================================================
asyncio.run(scan_and_connect())