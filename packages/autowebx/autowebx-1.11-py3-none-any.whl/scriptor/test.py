if __name__ == '__main__':
    try:
        init()
        threads = int_input('Threads: ')
        total = int_input('Total: ')
        proxy_enable = int_input('Proxy enable? (1/0): ', 0) == 1
        files = ['data.json']

        if proxy_enable:
            proxies = load('proxy.txt')
            files.append('proxy.txt')

        asd = AutoSaveDict('data.json')

        run = Run("<API-KEY>", {
            'threads': threads,
            'total': total,
            'proxy_enable': proxy_enable,
        }, *files)

        handle_threads(threads, total, Task)

        run.done()
    except Exception as er:
        sync_print(f'{Fore.RED}{er.__class__.__name__}: {er} ({exception_line()}){Fore.RESET}')