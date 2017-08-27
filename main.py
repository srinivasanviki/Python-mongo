from ReadUserReview.user_profile import user_profiling
if __name__=="__main__":
    user_profile=user_profiling()
    user_profile.drop_collection()
    user_profile.insert_profile()
    user_profile.update_scores()
    user_profile.create_reviews_table()
    user_profile.create_output_user_table()