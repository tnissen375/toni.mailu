# toni.mailu
Ansible role to setup mailu stack. https://mailu.io

```bash
ansible-playbook ./mailu.yml -i inventories --vault-id mailu@vault --tags "mailu" --extra-vars "dns_create=true"
```
