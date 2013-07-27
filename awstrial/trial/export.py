from trial.models import Instances
from django.contrib.auth.models import User


def get_marketing_opt_in_users(created_after=None):
    """
    Returns a list of user data dicts corresponding to users who have opted
    into receiving marketing material
    """
    user_data = []
    collected = []
    # Since the user is only presented with the option to opt-in at the point
    # of running a new instance, we have to check by instance
    if created_after:
        users = []
        instances = Instances.objects.filter(reservation_time__gte=created_after)
        for instance in instances:
            users.append(instance.owner)
    else:
        users = User.objects.all()

    for user in users:
        if user.username not in collected and user.get_profile().opt_marketing:
            user_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'created': user.date_joined,
            })
            collected.append(user.username)

    return user_data
