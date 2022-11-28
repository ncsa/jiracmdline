# jiracmdline
Cmdline interface to Jira

# Quick start
1. Start Docker container
```
curl -o go_jira.sh https://raw.githubusercontent.com/ncsa/jiracmdline/main/go.sh
bash ./go_jira.sh
```

### View task details
```
./summary.py svcplan-2023 svcplan-2467
```

### View Epic-Story-Task tree
```
./summary.py --recurse svcplan-2023
```

### Link sub-Tasks as children of their parent
```
./mk_children_from_subtasks.py --help
./mk_children_from_subtasks.py SVCPLAN-200 SVCPLAN-201 SVCPLAN-202
./mk_children_from_subtasks.py SVCPLAN-{300..305}
./mk_children_from_subtasks.py --parents SVCPLAN-101 SVCPLAN-157
```

### Add "linked children" to the same epic as their parent
```
./add_linked_children_to_epic.py SVCPLAN-200 SVCPLAN-201 SVCPLAN-202
./add_linked_children_to_epic.py SVCPLAN-{300..305}
./add_linked_children_to_epic.py --parents SVCPLAN-101 SVCPLAN-157
```

### Find all linked children that don't have an epic
... (and add them to their respective parent's epic)
```
./add_linked_children_to_epic.py --dryrun --project SVCPLAN
./add_linked_children_to_epic.py --project SVCPLAN
```

### Create linked children from description (also add to parent's epic)
Will read bulleted list, numbered list, or plain lines
(each line becomes a single child Task)
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
