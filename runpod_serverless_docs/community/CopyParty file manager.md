> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# CopyParty file manager

> Web-based GUI for easy file browsing, uploading, downloading, and media viewing on Runpod

# Setting up CopyParty on Runpod

CopyParty provides a webbased GUI that makes file management simple on Runpod instances. With its intuitive interface, you can browse directories, upload/download files, preview images and videos, and manage your Pod's filesystem without complex command-line operations.

## About CopyParty

CopyParty is an open-source project created that provides a portable file server with a web UI. It's perfect for managing files on cloud GPU instances where traditional file transfer methods might be cumbersome.

For a video demonstration, you can watch the [creator's YouTube tutorial](https://youtu.be/15_-hgsX2V0?si=AXArKvI79LEscpNn).

<Note>
  Check the repository for additional features, updates, and documentation: [github.com/9001/copyparty](https://github.com/9001/copyparty)
</Note>

## Requirements

To use CopyParty on Runpod, you need:

- **Terminal access to your Pod** - Either through web terminal or Jupyter Labs terminal.
- An available HTTP port on your Pod.
- A supported OS in the Docker base image.

<Note>
  CopyParty has been tested on Ubuntu-based Docker images and Runpod Official templates. When using custom templates or alternative Docker bases (like Python Slim) you may encounter file system dependency errors. Refer to the [GitHub repository](https://github.com/9001/copyparty) for details on OS support.
</Note>

### Verifying terminal access

You can access the terminal in two ways:

#### Option 1: Web terminal

If you see this option when clicking "Connect" on your Pod page, you have web terminal access:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=60c1c497e84560bd78943ecf11de12e5" alt="Web Terminal Access" data-og-width="1192" width="1192" data-og-height="486" height="486" data-path="community-solutions/copyparty-file-manager/webterminal.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=395594ae2be4f2ab7e999d4294c1c2e3 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=725372b8a18b8606e9d5b4455b805086 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=b952adf63d0b60f87cf85504801ef98e 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=4348757d92341b155d95a029a099ec44 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=ed5b2e9ef3e069bed9cab71bebbd55da 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/webterminal.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=2c20cffabfe503805da69c9f4660fa25 2500w" />

#### Option 2: JupyterLab terminal

If you have JupyterLab installed on your Pod, you can access the terminal there:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=9ee21e604bf1fbeedb0ae7b83c1a0e64" alt="JupyterLab Terminal" data-og-width="1906" width="1906" data-og-height="1292" height="1292" data-path="community-solutions/copyparty-file-manager/labsterminal.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=b92a17d7f2b015e7396339035f92dab6 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=a55d6d9c999b19abb5e868014c268de7 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=d1b40d638d3e42f9accd7541d7c42f81 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=238d380d8915e296a2894f2498431bd5 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=47eb4c9a492fcd2c501ad74f369876e9 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/labsterminal.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=ce4b3ac7538267853c5b22760f232414 2500w" />

## Installation steps

### Step 1: Access your Pod settings

Navigate to your Pod page and locate the settings:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=a95f3151465eb529b1c4679fb25333a4" alt="Edit Pod Settings" data-og-width="2324" width="2324" data-og-height="796" height="796" data-path="community-solutions/copyparty-file-manager/edit.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=91c49aabeb0c4c77267ff63cee5d6a17 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=788272fb81b0c17f1c8b53cccc0313b3 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=960e6b523f219e503fdfaa00b63d2a5f 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=a5ab718f8442bd812e0d5b1a28dbe57f 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=a40f7c5bac4211cf8ea2392759d2cb6d 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/edit.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=f32907c86603052a9d2e1ad6b8d9af00 2500w" />

### Step 2: Add an HTTP port

<Warning>
  **Adding a new port will restart your Pod and erase any data not stored in `/workspace`**

Before proceeding, ensure all important files are saved in `/workspace` or backed up elsewhere. Any installed libraries or files outside of `/workspace` will be lost.
</Warning>

Add a dedicated HTTP port for the CopyParty interface. If port 8888 is already in use (common for Jupyter), try port 8000 or another available port.

<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=33364a32c67b1bdcc652019fc6d13fbf" alt="Add HTTP Port" data-og-width="1686" width="1686" data-og-height="1046" height="1046" data-path="community-solutions/copyparty-file-manager/addhttp.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=f41b38ac68898b6158438d540e6e2f7b 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=4616f6dcef2c437a4fd8055c8b9cb0a3 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=b906b006bd77ece7b8d472be79646a93 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=e4872e5458616b7c837f3d348e3c728b 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=9b0bc9bcea2be1cdde101bcee088bded 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/addhttp.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=3d71d8c24eeb166a0ac42674b79ce68f 2500w" />

### Step 3: Install and run CopyParty

Open your terminal (web terminal or Jupyter terminal) and run one of the following commands:

#### Option 1: Standard installation

Run CopyParty directly (the session will end if you close the terminal):

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env && uv tool run copyparty -p 8000 --allow-csrf
```

Replace `-p 8000` with your chosen port number if different.

#### Option 2: Background installation with tmux

To keep CopyParty running even after closing the terminal, use `tmux`:

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
apt-get update && apt-get install tmux -y && tmux new-session -d -s copyparty 'curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env && uv tool run copyparty -p 8000 --allow-csrf' && tmux attach -t copyparty
```

<Info>
  **What is tmux?**

`tmux` (terminal multiplexer) is a tool that lets you run terminal sessions in the background. Think of it as a way to keep programs running even after you close your terminal window, like minimizing an app instead of closing it. This is particularly useful on Runpod where you want CopyParty to keep running even if you disconnect.

For a more in-depth tmux tutorial, check out this [comprehensive video guide](https://youtu.be/nTqu6w2wc68?si=OcI3qbh2kGH7_3fh).
</Info>

This command:

1. Installs tmux (a terminal multiplexer)
2. Creates a new tmux session named "copyparty"
3. Runs CopyParty in the background
4. Attaches you to the session to see the output

<Tip>
  **Quick tmux Commands**

- To detach from tmux and leave CopyParty running: Press `Ctrl+B` then `D`
- To reattach to the session later: `tmux attach -t copyparty`
- To stop CopyParty: Reattach and press `Ctrl+C`
  </Tip>

### Step 4: Access the CopyParty interface

Once CopyParty is running, click on the port number in your Runpod dashboard:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=e0475632ce4077ca54b5b090c51f9264" alt="Access Port" data-og-width="1216" width="1216" data-og-height="836" height="836" data-path="community-solutions/copyparty-file-manager/port.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=74707036204cc47e89255b08958aeddd 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=1928d30c39d626c9288b6676e666f0e0 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=f9c812a5d8249393c77364feeab3ba97 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=a7a5178aa4d0a88a805976473ed2a3c1 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=e2a91cad485e06d33852f2f10a152128 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/port.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=3e72281be77ff13822613a61d942551a 2500w" />

## Using CopyParty

### File navigation

The interface displays your file system on the left side:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=939b310e1a49cfd8e2d93e02b6ac4e9f" alt="Directory View" data-og-width="2864" width="2864" data-og-height="1312" height="1312" data-path="community-solutions/copyparty-file-manager/directory.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=ad26597fc4aa59929946cbd378c3eec4 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=ddbba50a14e03f325c552c2a2645cbb1 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=d8781f6f560fc3eff3400f58b021a563 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=46c40ac156e54655e13dd1a7ac45e89c 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=6b7622e76886a22c3f59340d67c99f48 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/directory.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=b8728fe25eb49ec1d022bf30257f8965 2500w" />

### Uploading files

Simply drag and drop files into the interface to upload them:
<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=58e4d3b3e8326d33a0fb06ef5ddbb331" alt="Upload Files" data-og-width="2840" width="2840" data-og-height="1566" height="1566" data-path="community-solutions/copyparty-file-manager/upload.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=2f8af92f2841b4cf88200a0f3c27b476 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=7560db31080c934968c8d9ffcf0d97b3 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=d92d9aaa46c79089b966cda2f1fd8c2d 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=1021ce3cc92b5a5ae0e18074992f5e31 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=f6db3894e43978afd015ca73c7aaada7 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/upload.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=04af41e9ef13da8d2a790e8a1a56c9a3 2500w" />

### Downloading files

To download files:

1. Click on files to select them (they'll be highlighted in pink)
2. Use the buttons in the bottom right:
   - **"dl"** - Download individual files
   - **"zip"** - Download multiple files as a zip archive

<img src="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=da85542b20047366e81e96c4467d7930" alt="Download Files" data-og-width="2326" width="2326" data-og-height="1154" height="1154" data-path="community-solutions/copyparty-file-manager/download.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=280&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=7dca48c2075cd1eb3a3169badb1c9fd7 280w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=560&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=d15ee02c701feb59eb9889881b2806da 560w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=840&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=50091674ce3b4e9548341ef05a8cc9c1 840w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=1100&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=c84c5b82980ee6369e0748f5bcbed50c 1100w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=1650&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=76e19b21de56f22d3305b38b104af7da 1650w, https://mintcdn.com/runpod-b18f5ded/QcR4sHy3480YmZ2d/community-solutions/copyparty-file-manager/download.png?w=2500&fit=max&auto=format&n=QcR4sHy3480YmZ2d&q=85&s=3ccde28897a954446129f8d3083142d5 2500w" />

## Tips and best practices

1. **Data Persistence**: Always store important files in `/workspace` to survive pod restarts
2. **Port Selection**: Choose a port that doesn't conflict with other services (avoid 8888 if using Jupyter)
3. **Large Files**: CopyParty handles large file transfers well, making it ideal for model weights and datasets

## Troubleshooting

### Session ends when terminal closes

Use the tmux option (Option 2) to keep CopyParty running in the background

## Alternative file transfer methods

While CopyParty provides an excellent web-based solution, Runpod also supports:

- Direct SSH/SCP transfers (if SSH is enabled)
- JupyterLab file browser
- [Runpod CLI](/runpodctl/overview) tool
- [Cloud storage integration](/pods/storage/cloud-sync) (S3, Google Drive, etc.)

Choose the method that best fits your workflow and security requirements.
