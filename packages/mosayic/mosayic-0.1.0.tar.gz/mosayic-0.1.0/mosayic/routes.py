

########### Firebase auth routes ##############

# @router.get("/admin/auth/users", response_model=list[FirebaseAuthUser])
# async def get_users(users: list = Depends(get_users_list)):
#     """
#     Get a list of all Firebase users. This route is only accessible to admins.
#     """
#     # TODO users pagination
#     return users


# @router.get("/admin/auth/users/{user_uid}", response_model=FirebaseAuthUser)
# async def get_user_by_id(users: list = Depends(get_firebase_user_by_uid)):
#     """
#     Get a Firebase user by their UID. This route is only accessible to admins.
#     """
#     return users


# @router.post("/admin/auth/delete-user/{user_uid}", dependencies=[Depends(delete_user)])
# async def admin_user_delete() -> None:
#     pass
