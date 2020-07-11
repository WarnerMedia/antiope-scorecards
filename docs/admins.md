# Admin Management

To grant/revoke a user's admin privileges, you must update their record in the users DynamoDB table. To do this, complete the following steps:

1. Open the AWS console to the account in which the database infrastructure is deployed, and navigate to DynamoDB.
1. Once you're in the DynamoDB console, click on "Tables" on the left sidebar.
1. Search for the users table (it should follow the pattern `${ResourcePrefix}-${Stage}-users-table`) and click on it. You should then be presented with an overview of the table.
1. Click on the "Items" tab towards the top of the page.
1. You'll be presented with the list of users within the system. To find the user you would like to manage, click on the "Scan" dropdown and change it to "Query."
1. You should see a new textbox for the value of the partition key (email) you would like to search for. Enter the email of the user you would like to manage in that textbox and click the "Start search" button.
1. Assuming your user exists in the database, you should be presented with one result. Click on that user.
1. If you see an `isAdmin` property on the user, you can update it to the desired value (`true` establishing the user as an admin, and `false` not). To update a property, click on the value of that property, your cursor should blink as if it was in a text box and you should be able to type the desired value there.
1. If you do not see `isAdmin`, click on one of the plus signs, and select "Insert," then "Boolean." Under the `FIELD`, type `isAdmin`. Under the `VALUE`, type either `true` or `false`.

Note: An admin is identified by the `isAdmin` property on their user record being `true`. Anything else (not present or `false`), will establish that user as not an admin.

Note2: Any users marked `isAdmin: true` will not be removed from the database if their record is removed from the user listed in the user import object in s3.
