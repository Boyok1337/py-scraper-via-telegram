import pandas as pd


def rate_candidates(file_path, skills_list, output_file):
    df = pd.read_csv(file_path)
    df["rating"] = 0

    for index, row in df.iterrows():
        candidate_skills = str(row["skills"]).split(",")
        rating = sum(
            1
            for skill in skills_list
            if skill.strip().lower() in [s.strip().lower() for s in candidate_skills]
        )
        df.at[index, "rating"] = rating

    sorted_df = df.sort_values(by="rating", ascending=False)

    sorted_df.to_csv(output_file, index=False)
    return sorted_df
