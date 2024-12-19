Blog Project.
--

 Phase 1: 

* Create Customized Adminstration site For Blog app.

* create superuser for the Adminstration (Blogger).

* Design Schama and Model of the Blog.

* Post:
  * Post should have a title, slug, author, body, publish ,created, updated, status.

  * Publish: the datetime indicates when the post was published.

  * created: the datetime indicates when the post was created.

  * updated: the datetime indicates the last time the post was updated.

  * status : have two choices ( Draft, Published )

* Understand ORM & QuerySets.

* Structure The app with Model-View-Template (MVT) Design Pattern.

* Create Functional Based View (FBV) to View all Post in the Blog.

  * understand FBV and How to inteact with Model and The Template.

* Create FBV to Create View for each Post.

* learn Models Managers  and create custom Manger to retrive only Published Posts.

* Post will be Created From the Blogger (Admin) site 

* Create a comments system.

  * use Django Forms to submit the comment for each Posts.

  * Forms content: name, email, body, created time, updated time, active.

  * each email can submit a comment each 30s to prevent spamming bots.

  * Detect and censored bad words.

  * if there is more than 3 bad words in a comment should be inactive.

  * This can be done on the View or Template level.

* create Templates to view all Posts and comments.

  * Learn Template syntax.

  * create base template and extend it.

* Posts Page

  * use django pagination to show only 3 Posts in each Page.

  * if we choose a post it should go to Post-detail page.

* Post-details

  * show the Post detail

  * show all prevoius comment

  * show form to sumbit new comment

----- 
Phase 2:
  * User system
    * create user system ( login, logout, register, forget password).
    * Use django.contrib.auth views, models to create the above system.
    * Create add/edit post views
      * each user can edit has own post only.
      * put the <add post>, login/logout in the header.

  * API Utilization
    * utilize https://gohper-blog-api.onrender.com/ APIs to feed the blog with Users/Posts/Comments..
    * Make a distinction between the posts from your blog and the one comming from the API.
    * Feed the API with the Blog Users/Posts/Comments ( optinal ).
   

  * Blog API
    * Create an API for the Blog models.
    * create serializers for each models.
    * user the correct API CBV for each request methods ( get, post, head, ..).
    * create an API endpoints.
    * Use the Token Authentication to Auth Read/Write operation.
      * only authenticated users can add posts.
      * only authenticeted author user can edit the posts that he/she created.
    
    * Gust User ( Anonymous User).
      * can't read/write Users.
      * can read-only the post ( can't add/edit).
      * can read/create Comments.
    
    * API Utilizer client (script).
      * create a small script that utilize the Blog API.
      
 ----- 
 Phase 3:
  *  Warning System
     * if the user enter more then 3 bad words, will get a warning, the comment will still inactive.
     * if the user got the third warning he will blocked from posting for 10 days.
     * use django messaging frameworks to notify the user when he got a warning.
     * prevernt the user from posting/editing if the user is blocked.

  * Tracking User Action & Limition System
    * The user can read only 3 posts a day.
    * If he enter the 4th post he should not view it.
    * the user can post 3 post a day only.
    * show the current vewing number for the post ( optinal ).
 
 * Like and subscribe system.
   * User can like/dislike/unlike posts.
   * User can subscribe/unsubscribe to user and get notify if the user post a new post.
   * If User is logged-in comment system should only have body and recive user name and email by the backend for the current user.
   * Blocked user can recive notification.

-----  
Phase 4:
 * ChatGPT integration:
   * User can generate new post by ChatGPT.
   * User can summarize any post by ChatGPT.
   * User can fix grammer/typo in his posts by ChatGPT.
   * User can search inside a post by ChatGPT ( optinal )

 * Sentiment analysis:
   * Use Hugging face models and APIs to do the sentiment analysis.
   * Choose the best hugging face model to do that.
   * Create a serverless lambda to analyze Posts and Comments.
   * Store the analysis back in the Blog app.

----- 
Phase 5:
 * Achievements and Badges:
   * Implement a system of achievements and badges for users based on their activities.
   * User must receive badges if:
     * The number of posts exceeded the powers of 10 (10, 100, 1000, .... ).
     * The number of likes on his posts exceeded the multiple of 100( 100, 200, 300).
     * the number of likes he did is the multiple of 500.
     * The number of logins as strikes by weeks.
 * Leaderboards:
   * Create leaderboards to showcase top contributors based on various metrics like the number of posts, likes received, or comments made

----- 
Phase 6:
 * Caching:
   * Implement caching mechanisms to improve the performance and responsiveness of the blog.
   * Utilize caching for frequently accessed data, such as blog posts, comments, and user information.
   * Cache database queries, API responses, and rendered views to reduce the load on the server and improve scalability.
   * Implement cache invalidation mechanisms to update cached data when changes occur.
   * Define appropriate cache expiration times for cached data to ensure freshness and prevent stale content.
   * Implement a manual trigger or API to invalidate the caches when the user wants.
   * Integrate Redis as a caching backend to improve the performance and scalability of the blog application.
     * use Redis locally with Docker.
     * Hosted Redis.
     * Redis cloud. 

----- 
Phase 7:
  * Room Chats using WebSockets
    * Create a Room chat for a user with at least 3 posts.
    * The user followers can see and join this chat room.
    * The users can see each other messages inside the room.
    * The subscribed user should be notified if the user opens a room for chat.
    * The owner user can kick any user from his room.
    * If the owner leaves the room, it should be closed, and remove everybody.
    * If the text that contains bad words should be hidden from all, only the owner and the sender can see it.
    * if the user did send more than 3 messages with bad words should be kicked immediately.

-----  
Phase 8:
 * ReactNative Blog App.
   * Create Login View.
   * After you login get the API token for the logged-in user, store it and use it in each request.
   * Create Views for each Blog API ( posts/ post-details).
   *  use React Query to fetch API data.
       * Use InfiniteQuery to get paginated data.
   * use FlashList instead of ScrollView.
   * Fetch paginated data on the scroll. 
   
   > Desgin is left to your imagination.

------

Workflow:
 * Push each Phase once complete, will have a partial review.
 * Do unit-testing as soon as possible in each Phase.
 * GitHub action
 * Deploy each phase when it is completed to a free hosting.
   * Use docker/docker-compose if needed to make it possible.
