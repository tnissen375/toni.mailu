# toni.mailu
Ansible role to setup mailu. See https://mailu.io for original project and other deploy options. 

There are config options for antivirus, calmav, admin und webmail. By now its "all or nothing". 
If you wanna install only a part of the toni.mailu stack you have to test on your on i had no time for fixing or testing this behavior. Seems the start.py scripts of the mailu containers need some investigation.

```bash
ansible-playbook ./mailu.yml -i ../<inventory_dir>/<inventory_name> --vault-id mailu@vault  --vault-id corteza@vault2 --extra-vars "ansible_ssh_host=<ip> mailu_webmail_type=roundcube nginx_domain=<domian_name_mailu> corteza_domain=<domain where corteza lives>" --tags "mailu" --extra-vars "dns_create=false"
```