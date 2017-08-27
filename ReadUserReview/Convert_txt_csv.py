profiles=["profile1","profile-hover1-60-70","profile-hover1-70-80","profile-hover1-80-100","profile-hover1-100-110","trip-Sentosa_user_review1-55-60","trip-Sentosa_user_review1-60-70","trip-Sentosa_user_review1-70-80","trip-Sentosa_user_review1-80-100","trip-Sentosa_user_review1-100-110","trip-universal-55-60","trip-universal-60-70","trip-universal-70-80","trip-universal-80-100","trip-universal-100-110"]



import csv
def write_csv_from_txt(objects):

    for object in objects:
        if "profile" in object:
            filename="profile.csv"
        elif "Sentosa" in object:
            filename="reviews.csv"
        elif "universal"in object:
            filename="universal.csv"

        with open('./csv/%s'%(filename), 'ab') as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow([])
            with open("./csv/%s.txt"%(object),"rb") as f:
                for line in f:
                    spamwriter.writerow(line.split("|"))




write_csv_from_txt(profiles)

