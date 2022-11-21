# jiracmdline
Cmdline interface to Jira

# Quick start
1. Start Docker container
```
curl -O https://raw.githubusercontent.com/ncsa/jiracmdline/main/go.sh
bash ./go.sh
```
1. Link sub-Tasks as children of their parent
```
cd /srv
./subtask_link_as_child.py --help
./subtask_link_as_child.py SVCPLAN-200 SVCPLAN-201 SVCPLAN-202
./subtask_link_as_child.py SVCPLAN-{300..305}
./subtask_link_as_child.py --parents SVCPLAN-101 SVCPLAN-157
```
1. Add "linked children" to the same epic as their parent
```
./add_linked_children_to_epic.py SVCPLAN-200 SVCPLAN-201 SVCPLAN-202
./add_linked_children_to_epic.py SVCPLAN-{300..305}
./add_linked_children_to_epic.py --parents SVCPLAN-101 SVCPLAN-157
```
1. Find all linked children that don't have an epic
```
./add_linked_children_to_epic.py --project SVCPLAN
```
1. Create linked children from description (also add to parent's epic)
```
./mk_children_from_description.py SVCPLAN-2511
```

# Dev Setup
1. Start Docker container
```
git clone https://github.com/ncsa/jiracmdline
cd jiracmdline
./go.sh
# now inside container
cd /home/working/jiracmdline
./devsetup.sh
```
1. Run test (inside Docker container)
```
cd /home/working/jiracmdline
./run.sh test.py
```
1. Run live iPython notebook (inside Docker container)
```
cd /home/working/jiracmdline
./jirashell.sh
```
