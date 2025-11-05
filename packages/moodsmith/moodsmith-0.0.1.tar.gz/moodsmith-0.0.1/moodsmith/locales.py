"""Holds message templates"""

POSITIVE_TEMPLATES = {
    "es": [
        (
            "Steve Jobs dijo que una computadora enseña a todos a pensar, "
            "y de hecho estás pensando{punct}"
        ),
        "Estás haciendo un trabajo excelente{punct}",
        "Los pequeños pasos se suman, y sin duda tú estás sumando{punct}",
        "Me encanta el progreso{punct} - Sigue adelante",
    ],
    "en": [
        (
            "Steve Jobs said a computer teaches everyone to think, "
            "and you are indeed thinking{punct}"
        ),
        "You are doing a great job{punct}",
        "Tiny steps add up, and you are certainly adding{punct}",
        "Love the progress{punct} - Keep going",
    ],
    "fr": [
        (
            "Steve Jobs disait qu'un ordinateur apprend à chacun à penser, "
            "et vous êtes effectivement en train de penser{punct}"
        ),
        "Vous faites un excellent travail{punct}",
        (
            "Les petits pas s'accumulent, "
            "et vous y contribuez certainement{punct}"
        ),
        "J'adore les progrès{punct} - continuer toujours",
    ],
}

MOTIVATIONAL_TEMPLATES = {
    "en": {
        "soft": [
            "Progress, not perfection—ship the next small improvement.",
            "You're learning every time the code runs, even when it fails.",
            "Tiny commits today become big momentum tomorrow.",
            "Be kind to yourself—debugging takes patience.",
            "Every clean refactor is a gift to your future self.",
        ],
        "medium": [
            "Mastery is built on reps—write, test, repeat.",
            "Feedback is fuel; tests are the engine.",
            "If you can explain it, you can build it.",
            "Read the errors like clues, not verdicts.",
            "When in doubt, make it smaller and make it pass.",
            "Experience is the name everyone gives to their mistakes. - Oscar Wilde",
            "If, at first, you do not succeed, call it version 1.0. ― Khayri R.R. Woulfe",
            "Confusion is part of programming. ― Felienne Hermans"
        ],
        "hard": [
            "Courage is a green test after a brutal red.",
            "You don't need perfect—ship, learn, iterate.",
            "Make the diff. Review. Improve. Repeat.",
            "If it hurts, automate it. If it breaks, test it.",
            "Discipline beats inspiration: show up and push a commit.",
            "It's not a bug; it's an undocumented feature. - Grace Hopper",
            "Talk is cheap. Show me the code. ― Linus Torvalds"
        ],
    },

    "es": {
        "soft": [
            "Progreso, no perfección: entrega la próxima mejora pequeña.",
            "Cada vez que el código corre, aprendes, incluso cuando falla.",
            "Pequeños commits hoy se vuelven gran impulso mañana.",
            "Sé paciente contigo—depurar requiere calma.",
            "Cada refactor limpio es un regalo para tu yo del futuro.",
        ],
        "medium": [
            "La maestría se construye con repeticiones: escribir, probar, repetir.",
            "La retroalimentación es combustible; las pruebas son el motor.",
            "Si puedes explicarlo, puedes construirlo.",
            "Lee los errores como pistas, no como veredictos.",
            "Cuando dudes, hazlo más pequeño y haz que pase.",
        ],
        "hard": [
            "El coraje es un test en verde después de un rojo brutal.",
            "No necesitas perfección—entrega, aprende, itera.",
            "Haz el diff. Revisa. Mejora. Repite.",
            "Si duele, automatízalo. Si se rompe, pruébalo.",
            "La disciplina supera a la inspiración: preséntate y haz un commit.",
        ],
    },

    "fr": {
        "soft": [
            "Le progrès avant la perfection — livre la prochaine petite amélioration.",
            "Tu apprends à chaque exécution du code, même quand ça échoue.",
            "De petits commits aujourd'hui deviennent un grand élan demain.",
            "Sois patient avec toi-même — le débogage demande du temps.",
            "Chaque refactorisation propre est un cadeau pour ton futur toi.",
        ],
        "medium": [
            "La maîtrise se construit par la répétition : écrire, tester, recommencer.",
            "Le feedback est le carburant ; les tests sont le moteur.",
            "Si tu peux l'expliquer, tu peux le construire.",
            "Lis les erreurs comme des indices, pas des verdicts.",
            "En cas de doute, fais plus petit et fais passer le test.",
        ],
        "hard": [
            "Le courage, c'est le test qui passe au vert après un rouge brutal.",
            "Pas besoin d'être parfait — livre, apprends, itère.",
            "Fais le diff. Relis. Améliore. Répète.",
            "Si ça fait mal, automatise-le. Si ça casse, teste-le.",
            "La discipline bat l'inspiration : sois présent et fais un commit.",
        ],
    },
}

NEGATIVE_MOTIVATIONAL = {
    "en": {
        "soft": [
            (
                "tiny steps are still steps. "
                "standing still like you are isn't{punct}"
            ),
            "come on. A little effort won't kill you{punct}",
            (
                "thinking about it is cute, "
                "but actually doing it would be impressive{punct}"
            ),
            "your comfort zone is cozy. so is mediocrity{punct}",
            "you don't need more time. you need fewer excuses{punct}",
            "you could have finished this by now. instead, here we are{punct}",
            (
                "maybe if you started, "
                "you wouldn't still be thinking about starting{punct}"
            )
        ],
        "medium": [
            "look at you, doing nothing yet again. iconic{punct}",
            "if you're tired of restarting, try not quitting for once{punct}",
            (
                "I'm sure thinking about getting "
                "things done is going to help{punct}"
            ),
            "this isn't getting any easier while you wait{punct}",
            "waiting for motivation is a hobby at this point{punct}",
            "future you here. Please start now{punct}",
            "you haven't failed yet. But you sure are getting close{punct}"
        ],
        "hard": [
            "your comfort zone called. It says you've never left{punct}",
            "your goals miss you. They haven't seen you in a while{punct}",
            "with your work ethic, your potential is just a rumour{punct}",
            "if you keep this up you'll prove your haters right{punct}",
            (
                "you don't need to rush. "
                "It's not like your life is finite or anything{punct}"
            ),
            "if effort was money, you'd be broke{punct}",
            "your future self is watching. They're disappointed{punct}"
        ]
    },
    "fr": {
        "soft": [
            (
                "même les petits pas restent des pas. "
                "Rester immobile comme tu le fais n'en est pas{punct}"
            ),
            "allez. Un petit effort ne va pas te tuer{punct}",
            (
                "y penser c'est mignon, "
                "mais le faire pour de vrai serait impressionnant{punct}"
            ),
            "ta zone de confort est agréable. La médiocrité aussi{punct}",
            (
                "tu n'as pas besoin de plus de temps. "
                "Tu as besoin de moins d'excuses{punct}"
            ),
            (
                "tu aurais pu finir ça depuis longtemps. "
                "À la place, nous voilà{punct}"
            ),
            (
                "peut-être que si tu avais commencé, "
                "tu ne serais pas encore en train d'y penser{punct}"
            )
        ],
        "medium": [
            "regarde-toi, à ne rien faire encore une fois. Iconique{punct}",
            (
                "si tu es fatigué de recommencer, "
                "essaie de ne pas abandonner pour une fois{punct}"
            ),
            (
                "je suis sûr que penser à "
                "faire les choses va beaucoup aider{punct}"
            ),
            "ça ne devient pas plus facile en attendant{punct}",
            "attendre la motivation est devenu un passe-temps{punct}",
            "futur toi ici. S'il te plaît, commence maintenant{punct}",
            (
                "tu n'as pas encore échoué. "
                "Mais tu t'en rapproches sérieusement{punct}"
            )
        ],
        "hard": [
            (
                "ta zone de confort a appelé. "
                "Elle dit que tu n'en es jamais sorti{punct}"
            ),
            (
                "tes objectifs te manquent. "
                "Ils ne t'ont pas vu depuis un moment{punct}"
            ),
            (
                "avec ton éthique de travail, ton "
                "potentiel n'est qu'une rumeur{punct}"
            ),
            (
                "si tu continues comme ça, tu donneras "
                "raison à tes détracteurs{punct}"
            ),
            (
                "tu n'as pas besoin de te presser. C'est pas comme "
                "si ta vie était finie ou quoi que ce soit{punct}"
            ),
            "si l'effort valait de l'argent, tu serais pauvre{punct}",
            "ton futur toi te regarde. Il est déçu{punct}"
        ]
    },
    "es": {
        "soft": [
            (
                "los pasos pequeños siguen siendo pasos. "
                "quedarse quieto como lo haces no lo es{punct}"
            ),
            "vamos. Un poco de esfuerzo no te va a matar{punct}",
            (
                "pensarlo es lindo, "
                "pero hacerlo de verdad sería impresionante{punct}"
            ),
            "tu zona de confort es cómoda. la mediocridad también{punct}",
            "no necesitas más tiempo. necesitas menos excusas{punct}",
            "podrías haber terminado esto ya. en cambio, aquí estamos{punct}",
            (
                "tal vez si empezaras, "
                "no seguirías pensando en empezar{punct}"
            )
        ],
        "medium": [
            "mirarte, sin hacer nada otra vez. icónico{punct}",
            (
                "si estás cansado de reiniciar, "
                "intenta no rendirte por una vez{punct}"
            ),
            (
                "estoy seguro de que pensar en "
                "hacer las cosas va a ayudar mucho{punct}"
            ),
            "esto no se hace más fácil mientras esperas{punct}",
            "esperar motivación ya es un pasatiempo a estas alturas{punct}",
            "el tú del futuro aquí. Por favor, empieza ahora{punct}",
            "aún no has fallado. Pero te estás acercando peligrosamente{punct}"
        ],
        "hard": [
            "tu zona de confort llamó. Dice que nunca la has dejado{punct}",
            "tus metas te extrañan. Hace tiempo que no te ven{punct}",
            "con tu ética de trabajo, tu potencial es solo un rumor{punct}",
            "si sigues así, le darás la razón a tus detractores{punct}",
            (
                "no necesitas apurarte. "
                "No es como si tu vida fuera finita o algo así{punct}"
            ),
            "si el esfuerzo fuera dinero, estarías en bancarrota{punct}",
            "tu yo del futuro te está observando. Está decepcionado{punct}"
        ]
    }
}


FUNNY_TEMPLATE = {
    "en": [
       " Computers are fast; developers keep them slow{punct}",

"If debugging is the process of removing bugs,"
" then programming must be the process of putting them in{punct}",

"You should name a variable using the same"
" care with which you name a first-born child{punct}",

"Any code of your own that you haven`t "
"looked at for six or more months might "
"as well have been written by someone else{punct}",

"Always code as if the guy who ends up"
" maintaining your code will be a violent "
"psychopath who knows where you live{punct}",

"We like to think we spend our time power"
" typing, but we actually spend most of "
"our time staring into the abyss{punct}"
   ],

   "fr": [
    " Les ordinateurs sont rapides ; "
    "les développeurs les ralentissent{punct}",

"Si le débogage consiste à supprimer "
"les bogues, la programmation consiste à les introduire{punct}",

"Il faut nommer une variable avec "
"autant de soin que l'on nomme son premier-né{punct}",

"Tout code que vous n'avez pas relu"
" depuis six mois ou plus pourrait tout "
"aussi bien avoir été écrit par quelqu'un d'autre{punct}",

"Codez toujours comme si celui qui "
"finira par maintenir votre code était"
" un psychopathe violent qui connaît votre adresse{punct}",

"On aime croire qu'on passe notre "
"temps à taper vite, mais en réalité, on "
"passe le plus clair de notre temps à fixer l'abîme{punct}"
   ],
   "es": [
       "Las computadoras son rápidas; "
       "los desarrolladores las ralentizan{punct}",

"Si depurar se trata de eliminar "
"errores, programar se trata de introducirlos{punct}",

"Deberías nombrar una variable "
"con el mismo cuidado con el que "
"nombrarías a tu primogénito{punct}",

"Cualquier código que no hayas"
" revisado en seis meses o más bien podría "
"haber sido escrito por otra persona{punct}",

"Siempre programa como si la"
" persona que eventualmente mantendrá tu "
"código fuera un psicópata violento que conoce tu dirección{punct}",

"Nos gusta pensar que pasamos el tiempo escribiendo "
"rápido, pero en realidad, pasamos la mayor parte"
" del tiempo mirando al abismo{punct}"
   ]
}
