using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

namespace SteaMRogueWorker
{
    class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine("{\"error\": \"Usage: SAMWorker.exe get <appid> OR SAMWorker.exe set <appid> [ids]\"}");
                return 1;
            }

            string action = args[0].ToLowerInvariant();
            long appId;
            if (!long.TryParse(args[1], out appId))
            {
                Console.WriteLine("{\"error\": \"Invalid appid\"}");
                return 1;
            }

            try
            {
                string dir = AppDomain.CurrentDomain.BaseDirectory;
                string samApiPath = Path.Combine(dir, "SAM.API.dll");
                string samGamePath = Path.Combine(dir, "SAM.Game.exe");

                Assembly samApiAsm = Assembly.LoadFrom(samApiPath);
                Assembly samGameAsm = Assembly.LoadFrom(samGamePath);

                var client = new SAM.API.Client();
                client.Initialize(appId);

                Type mgrType = samGameAsm.GetType("SAM.Game.Manager");
                object manager = Activator.CreateInstance(mgrType, (long)appId, client);

                MethodInfo refreshMethod = mgrType.GetMethod("RefreshStats", BindingFlags.NonPublic | BindingFlags.Instance);
                if (refreshMethod != null)
                {
                    refreshMethod.Invoke(manager, new object[0]);
                }

                FieldInfo listField = mgrType.GetField("_AchievementListView", BindingFlags.NonPublic | BindingFlags.Instance);
                ListView listView = null;

                for (int i = 0; i < 40; i++)
                {
                    client.RunCallbacks(false);
                    Thread.Sleep(100);
                    if (listField != null)
                    {
                        listView = listField.GetValue(manager) as ListView;
                        if (listView != null && listView.Items.Count > 0)
                        {
                            break;
                        }
                    }
                }

                if (listView == null)
                {
                    Console.OutputEncoding = System.Text.Encoding.UTF8;
                    Console.WriteLine("{\"error\": \"Failed to retrieve achievement list\"}");
                    return 2;
                }

                Type infoType = samGameAsm.GetType("SAM.Game.Stats.AchievementInfo");
                FieldInfo idField = infoType.GetField("Id");
                FieldInfo nameField = infoType.GetField("Name");
                FieldInfo descField = infoType.GetField("Description");
                FieldInfo isAchievedField = infoType.GetField("IsAchieved");
                FieldInfo iconNormalField = infoType.GetField("IconNormal");
                FieldInfo iconLockedField = infoType.GetField("IconLocked");

                if (action == "get")
                {
                    var items = new List<string>();
                    foreach (ListViewItem item in listView.Items)
                    {
                        object info = item.Tag;
                        if (info == null) continue;

                        string id = (string)idField.GetValue(info) ?? "";
                        string name = (string)nameField.GetValue(info) ?? "";
                        string desc = (string)descField.GetValue(info) ?? "";
                        bool achieved = (bool)isAchievedField.GetValue(info);
                        string icon = (string)iconNormalField.GetValue(info) ?? "";
                        string iconLocked = (string)iconLockedField.GetValue(info) ?? "";

                        string itemJson = string.Format(
                            "{{\"id\":{0},\"name\":{1},\"desc\":{2},\"achieved\":{3},\"icon\":{4},\"icon_locked\":{5}}}",
                            EscapeJson(id),
                            EscapeJson(name),
                            EscapeJson(desc),
                            achieved ? "true" : "false",
                            EscapeJson(icon),
                            EscapeJson(iconLocked)
                        );
                        items.Add(itemJson);
                    }

                    Console.OutputEncoding = System.Text.Encoding.UTF8;
                    Console.WriteLine("{\"success\": true, \"achievements\": [" + string.Join(",", items.ToArray()) + "]}");
                    return 0;
                }
                else if (action == "set")
                {
                    string toUnlockStr = "";
                    if (args.Length > 2)
                    {
                        if (args[2] == "--stdin")
                        {
                            toUnlockStr = Console.In.ReadToEnd();
                        }
                        else if (File.Exists(args[2]))
                        {
                            toUnlockStr = File.ReadAllText(args[2]);
                        }
                        else
                        {
                            toUnlockStr = args[2];
                        }
                    }

                    var unlockSet = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                    if (!string.IsNullOrEmpty(toUnlockStr))
                    {
                        string[] parts = toUnlockStr.Split(new char[] { ',', '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                        foreach (string p in parts)
                        {
                            string trimmed = p.Trim();
                            if (!string.IsNullOrEmpty(trimmed))
                            {
                                unlockSet.Add(trimmed);
                            }
                        }
                    }

                    int modifiedCount = 0;
                    foreach (ListViewItem item in listView.Items)
                    {
                        object info = item.Tag;
                        if (info == null) continue;

                        string id = (string)idField.GetValue(info) ?? "";
                        bool achieved = (bool)isAchievedField.GetValue(info);
                        bool shouldBeUnlocked = unlockSet.Contains(id);

                        if (shouldBeUnlocked != achieved)
                        {
                            client.SteamUserStats.SetAchievement(id, shouldBeUnlocked);
                            modifiedCount++;
                        }
                    }

                    bool stored = client.SteamUserStats.StoreStats();
                    Console.OutputEncoding = System.Text.Encoding.UTF8;
                    Console.WriteLine(string.Format("{{\"success\": true, \"modified\": {0}, \"stored\": {1}}}", modifiedCount, stored ? "true" : "false"));
                    return 0;
                }
                else
                {
                    Console.OutputEncoding = System.Text.Encoding.UTF8;
                    Console.WriteLine("{\"error\": \"Unknown action\"}");
                    return 1;
                }
            }
            catch (Exception ex)
            {
                Console.OutputEncoding = System.Text.Encoding.UTF8;
                Console.WriteLine("{\"error\": " + EscapeJson(ex.ToString()) + "}");
                return 1;
            }
        }

        static string EscapeJson(string s)
        {
            if (s == null) return "\"\"";
            var sb = new System.Text.StringBuilder();
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '\\': sb.Append("\\\\"); break;
                    case '"': sb.Append("\\\""); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < ' ')
                        {
                            sb.AppendFormat("\\u{0:x4}", (int)c);
                        }
                        else
                        {
                            sb.Append(c);
                        }
                        break;
                }
            }
            sb.Append('"');
            return sb.ToString();
        }
    }
}
