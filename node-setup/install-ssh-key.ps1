# Installs your SSH public key on a freshly installed BC-250 node, then tests key login.
# Usage (PowerShell on your PC):  .\install-ssh-key.ps1 -Node 192.168.1.145 -Name bc250-3
# You type the node's password once; the script never stores it.
#
# -Name saves the node's host key under its name instead of its IP. The USB adapters
# (and so the IPs) can move between boards, and an IP-keyed entry would then clash.
param(
    [Parameter(Mandatory)][string]$Node,
    [string]$Name = $Node,
    [string]$User = 'server',
    [string]$PublicKey = "$env:USERPROFILE\.ssh\id_ed25519.pub"
)

$hostKeyAlias = "HostKeyAlias=$Name"
Write-Host "Installing $PublicKey on $User@$Node (host key saved as '$Name')"
Write-Host "At the fingerprint prompt, type 'yes' only if it matches the node's own screen:"
Write-Host "    ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub"
Write-Host ''

# tr -d '\r' strips the Windows line ending PowerShell adds when piping to ssh;
# restorecon gives ~/.ssh the SELinux labels sshd requires on Fedora.
Get-Content $PublicKey | ssh -o $hostKeyAlias "$User@$Node" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && tr -d '\r' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && restorecon -R ~/.ssh"
if ($LASTEXITCODE -ne 0) { Write-Host "Copying the key failed (exit $LASTEXITCODE)." -ForegroundColor Red; return }

# BatchMode forbids password prompts, so this only succeeds if the key works.
# No inner double quotes: Windows PowerShell 5.1 mangles them when passing arguments to ssh.
ssh -o BatchMode=yes -o $hostKeyAlias "$User@$Node" 'echo Key login OK: $(whoami)@$(hostname)'
if ($LASTEXITCODE -ne 0) { Write-Host 'Key login test failed.' -ForegroundColor Red }
