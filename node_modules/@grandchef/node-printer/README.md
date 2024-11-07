Node Printer Prebuild
============
Native bind printers on POSIX and Windows OS from Node.js, electron and node-webkit.

### Features:

* no dependecies;
* native method wrappers from Windows  and POSIX (which uses [CUPS 1.4/macOS 14](http://cups.org/)) APIs;
* compatible with node v0.8.x, 0.9.x and v0.11.x (with 0.11.9 and 0.11.13);
* compatible with node-webkit v0.8.x and 0.9.2;
* `getPrinters()` to enumerate all installed printers with current jobs and statuses;
* `getPrinter(printerName)` to get a specific/default printer info with current jobs and statuses;
* `getPrinterDriverOptions(printerName)` ([POSIX](http://en.wikipedia.org/wiki/POSIX) only) to get a specific/default printer driver options such as supported paper size and other info
* `getSelectedPaperSize(printerName)` ([POSIX](http://en.wikipedia.org/wiki/POSIX) only) to get a specific/default printer default paper size from its driver options
* `getDefaultPrinterName()` return the default printer name;
* `printDirect(options)` to send a job to a specific/default printer, now supports [CUPS options](http://www.cups.org/documentation.php/options.html) passed in the form of a JS object (see `cancelJob.js` example). To print a PDF from windows it is possible by using [node-pdfium module](https://github.com/tojocky/node-pdfium) to convert a PDF format into EMF and after to send to printer as EMF;
* `printFile(options)`  ([POSIX](http://en.wikipedia.org/wiki/POSIX) only) to print a file;
* `getSupportedPrintFormats()` to get all possible print formats for printDirect method which depends on OS. `RAW` and `TEXT` are supported from all OS-es;
* `getJob(printerName, jobId)` to get a specific job info including job status;
* `setJob(printerName, jobId, command)` to send a command to a job (e.g. `'CANCEL'` to cancel the job);
* `getSupportedJobCommands()` to get supported job commands for setJob() depends on OS. `'CANCEL'` command is supported from all OS-es.


### How to install:
```
npm install @grandchef/node-printer
# or
yarn add @grandchef/node-printer
```

### Step 2 —— rebuild by electron-builder to match node ABI

See [examples](https://github.com/grandchef/node-printer/tree/main/examples)

```bash
npx electron-builder install-app-deps
```

### Step 3 —— build native code for x64

> need to change dir into `node_modules/@namespace/node-printer` first

* Timo Kunze, @timokunze
* Thiago Lugli, @thiagoelg
* Eko Eryanto, @ekoeryanto

### Step 4 —— build native code for ia32

> still in the dir `node_modules/@namespace/node-printer`

```bash
node-pre-gyp rebuild --target_arch=ia32
node-pre-gyp build package --runtime=electron --target=`${electron_version}` --target_arch=ia32 --build-from-source
```

## Support
- If you have a problem, find/create a new [Github issue](https://github.com/grandchef/node-printer/issues)

## Refer

- [examples](https://github.com/grandchef/node-printer/tree/main/examples)
- [TimoKunze/node-printer](https://github.com/TimoKunze/node-printer)
- [thiagoelg/node-printer](https://github.com/thiagoelg/node-printer)
- [mapbox/node-sqlite3](https://github.com/mapbox/node-sqlite3)

## License

- [The MIT License (MIT)](http://opensource.org/licenses/MIT)
