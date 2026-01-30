    # @title ## Remove Staff users {"form-width":"20%"}

    #   Remove any users listed as Staff so the data only includes student data.
    #  
    #    Additional users removed:
    #           'travis@pdx.edu',
    #           'marie.snetinova@matfyz.cuni.cz',
    #           'mptl_group_1@pdx.edu',
    #           'mptl_group_2@pdx.edu',
    #           'mptl_group_3@pdx.edu',
    #           'mptl_group_4@pdx.edu',
    #           'mptl_group_5@pdx.edu',
    #           'mptl_group_6@pdx.edu',
    #           'mptl_group_1@pdx.edu',
    #           'mptl_user_1@pdx.edu',
    #           'mptl_user_10@pdx.edu'


from IPython.display import display

def remove_staff(u_df, 
                 t_df,
                 users_to_remove
                 ):

    # Generate a list of users where is_staff is TRUE from userprofile
    show_remove_staff_data = False # @param {"type":"boolean"}
    if 'is_staff' in u_df.columns:
        staff_users_df = u_df[u_df['is_staff'] == True]

        if 'username' in staff_users_df.columns:
            staff_user_ids = staff_users_df['username'].dropna().astype(str).tolist()
            staff_user_ids = staff_user_ids + users_to_remove

        print(f"Found {len(staff_user_ids)} staff users. IDs: {staff_user_ids}")
        # display(staff_users_df)

        # Remove any row from files from users on that list

        if 'username' in u_df.columns:
            u_df = u_df.rename(columns={'username': 'user'})
            print(f"Renaming 'username' column to 'user' in userprofile")

        if 'user' in t_df.columns:
            initial_chat_rows = len(t_df)
            no_staff_df = t_df[~t_df['user'].isin(staff_user_ids)]
            removed_chat_rows = initial_chat_rows - len(no_staff_df)
            t_df = no_staff_df
            print(f"Removed {removed_chat_rows} rows from transcript corresponding to staff users.")
            print(f"Updated transcript DataFrame after removing staff user entries.")

            if show_remove_staff_data:
                display(t_df)
        else:
            print(f"Warning: 'user' column not found in transcript DataFrame. Cannot remove staff user entries.")

    else:
        print(f"Warning: 'is_staff' column not found in the DataFrame. Cannot identify staff users.")
    return u_df, t_df