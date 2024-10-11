import random


def without_keys(d, keys):
    return {k: d[k] for k in d.keys() - keys}

def get_cpu_name(excluded: list):
    name_list = [
        # Male names
        "James", "John", "Robert", "Michael", "William",
        "David", "Richard", "Joseph", "Thomas", "Charles",
        "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
        "Donald", "Steven", "Paul", "Andrew", "Joshua",
        "Kevin", "Brian", "George", "Edward", "Ronald",
        "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob",
        "Gary", "Nicholas", "Eric", "Stephen", "Jonathan",
        "Larry", "Scott", "Frank", "Brandon", "Raymond",
        "Gregory", "Benjamin", "Samuel", "Patrick", "Alexander",
        "Jack", "Dennis", "Jerry", "Tyler", "Aaron",

        # Female names
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
        "Barbara", "Susan", "Jessica", "Sarah", "Karen",
        "Nancy", "Lisa", "Margaret", "Betty", "Sandra",
        "Ashley", "Dorothy", "Kimberly", "Emily", "Donna",
        "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
        "Stephanie", "Rebecca", "Laura", "Sharon", "Cynthia",
        "Kathleen", "Amy", "Shirley", "Angela", "Helen",
        "Anna", "Brenda", "Pamela", "Nicole", "Emma",
        "Samantha", "Katherine", "Christine", "Debra", "Rachel",
        "Catherine", "Carolyn", "Janet", "Maria", "Heather"
    ]
    randSeed = random.randint(0, len(name_list) - 1)
    chosen = name_list[randSeed]

    if chosen in excluded:
        return get_cpu_name(excluded)
    else:
        return chosen
