def get_levenshtein_matches(input_str, string_list):
    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            s1, s2 = s2, s1

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    max_distance = len(input_str) // 2
    result = {}

    for s in string_list:
        distance = levenshtein(input_str, s)
        if distance <= max_distance:
            result.setdefault(distance, []).append(s)

    return result


import csv

disc_names_fi = open("discord_thread_names.txt", "r")

disc_names = [_.replace("\n","").lower() for _ in disc_names_fi.readlines()]
disc_names_fi.close()

attendance_fi = open("data\cn-ca-fullerton_StudentAccessReport_2025-06-13.csv", "r")
_ = csv.reader(attendance_fi)
attendance_names = set([row[1].lower() for row in _])

attendance_fi.close()
print(disc_names)

for disc_name in disc_names:
    if disc_name in attendance_names:
        print(f"Found entry for {disc_name}")
    else:
        print(f"\tFailed search for {disc_name}, attempting fuzzy search")
        res = get_levenshtein_matches(disc_name, attendance_names)
        print(res)